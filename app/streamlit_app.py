"""Aplicação web local para revisar mapeamentos e preparar saídas de estoque/vendas.

Execute na raiz do projeto:
    streamlit run app/streamlit_app.py

Os mapeamentos são confirmados na interface. A saída usa modelos locais
configurados e os arquivos enviados são tratados em diretório temporário.
"""

from __future__ import annotations

import csv
from io import BytesIO
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import re
from time import perf_counter
import unicodedata

import pandas as pd
import streamlit as st

from data_intelligence.canonical import write_excel_template
from data_intelligence.dataset import Dataset
from data_intelligence.canonical.mapping import apply_column_mapping
from data_intelligence.ingestion import read_csv, read_excel
from data_intelligence.transforms import prepare_dataset


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEMO_DIR = PROJECT_ROOT / "data" / "synthetic" / "farmacia_demo"
DEFAULT_TEMPLATE_DIR = Path.home() / "Desktop" / "Banco de Dados" / "Modelos principais"
TEMPLATE_DIR = Path(os.environ.get("DATA_INTELLIGENCE_TEMPLATE_DIR", DEFAULT_TEMPLATE_DIR))

REPORT_CONFIGS: dict[str, dict[str, object]] = {
    "estoque": {
        "template_name": "estoque.xlsx",
        "demo_template": DEMO_DIR / "modelo_estoque_demo.xlsx",
        "sheet_name": "ESTOQUE",
        "fields": [
            "cnpj", "unidade", "mes", "ean", "descricao_produto", "grupo",
            "subgrupo", "laboratorio", "quantidade", "valor_total_custo",
            "data_cadastro", "data_ult_venda",
        ],
    },
    "vendas": {
        "template_name": "vendas.xlsx",
        "demo_template": DEMO_DIR / "modelo_vendas_demo.xlsx",
        "sheet_name": "VENDAS",
        "fields": [
            "cnpj", "unidade", "ean", "cod_reduzido", "mes", "descricao_produto",
            "grupo", "subgrupo", "laboratorio", "quantidade", "valor_total_bruto",
            "valor_total_liquido", "valor_total_custo",
        ],
    },
}

FIELD_LABELS = {
    "cnpj": "CNPJ",
    "unidade": "UNIDADE",
    "mes": "MÊS",
    "ean": "EAN",
    "cod_reduzido": "COD_REDUZIDO",
    "descricao_produto": "DESCRICAO_PRODUTO",
    "grupo": "GRUPO",
    "subgrupo": "SUBGRUPO",
    "laboratorio": "LABORATORIO",
    "quantidade": "QUANTIDADE",
    "valor_total_bruto": "VALOR_TOTAL_BRUTO",
    "valor_total_liquido": "VALOR_TOTAL_LIQUIDO",
    "valor_total_custo": "VALOR_TOTAL_CUSTO",
    "data_cadastro": "DATA_CADASTRO",
    "data_ult_venda": "DATA_ULT_VENDA",
}

FIELD_ALIASES = {
    "cnpj": ("CNPJ", "CNPJ da unidade", "Documento da filial"),
    "unidade": ("UNIDADE", "Nome da unidade", "Unidade"),
    "mes": ("MÊS", "MES", "Período", "Período de venda", "Mês de referência"),
    "ean": ("EAN", "GTIN", "GTIN do produto", "Identificador GTIN", "Código de barras", "Identificação do produto (GTIN)"),
    "cod_reduzido": ("COD_REDUZIDO", "Código reduzido", "Código interno", "Código do produto"),
    "descricao_produto": ("DESCRICAO_PRODUTO", "Descrição", "Produto", "Nome do produto", "Nome comercial", "Produto comercializado", "Item vendido"),
    "grupo": ("GRUPO", "Categoria", "Família"),
    "subgrupo": ("SUBGRUPO", "Departamento", "Subgrupo"),
    "laboratorio": ("LABORATORIO", "Laboratório", "Fabricante"),
    "quantidade": ("QUANTIDADE", "Estoque", "Saldo disponível", "Saldo físico", "Unidades comercializadas", "Qtd. vendida", "Volume vendido"),
    "valor_total_bruto": ("VALOR_TOTAL_BRUTO", "Total antes de descontos", "Valor original das vendas"),
    "valor_total_liquido": ("VALOR_TOTAL_LIQUIDO", "Venda", "Valor vendido", "Total líquido"),
    "valor_total_custo": ("VALOR_TOTAL_CUSTO", "Custo", "Montante em custo"),
    "data_cadastro": ("DATA_CADASTRO", "Data de cadastro"),
    "data_ult_venda": ("DATA_ULT_VENDA", "Data da última venda", "Última venda"),
}
REQUIRED_FIELDS = {"ean", "descricao_produto"}


def _normalize(value: object) -> str:
    text = unicodedata.normalize("NFKD", str(value).casefold())
    text = "".join(char for char in text if not unicodedata.combining(char))
    return re.sub(r"[^a-z0-9]+", " ", text).strip()


def _resolve_template(report_type: str) -> Path:
    config = REPORT_CONFIGS[report_type]
    local_template = TEMPLATE_DIR / str(config["template_name"])
    if local_template.is_file():
        return local_template
    return Path(config["demo_template"])


def _suggest_field_mapping(columns: list[str], report_type: str) -> dict[str, str]:
    """Sugere pares origem/campo usando aliases determinísticos revisáveis."""
    config = REPORT_CONFIGS[report_type]
    used_sources: set[str] = set()
    mapping: dict[str, str] = {}
    for canonical_field in config["fields"]:
        aliases = (FIELD_LABELS[canonical_field], *FIELD_ALIASES.get(canonical_field, ()))
        candidate = next(
            (
                column
                for alias in aliases
                for column in columns
                if column not in used_sources and _normalize(column) == _normalize(alias)
            ),
            None,
        )
        if candidate is not None:
            mapping[candidate] = canonical_field
            used_sources.add(candidate)
    return mapping


@st.cache_data(show_spinner=False)
def _validate_template(template_path: Path, report_type: str) -> None:
    config = REPORT_CONFIGS[report_type]
    template_columns = list(
        pd.read_excel(
            template_path,
            sheet_name=str(config["sheet_name"]),
            nrows=0,
        ).columns
    )
    expected_columns = [FIELD_LABELS[field] for field in config["fields"]]
    if [_normalize(column) for column in template_columns] != [
        _normalize(column) for column in expected_columns
    ]:
        raise ValueError(
            f"O modelo '{template_path.name}' não corresponde aos campos e à ordem esperados. "
            "Confira se selecionou o modelo correto."
        )


def detect_report_type(filename: str, headers: list[object]) -> tuple[str | None, str]:
    """Usa nome do arquivo e cabeçalhos para sugerir estoque ou vendas."""
    filename_key = _normalize(Path(filename).stem)
    if "estoque" in filename_key:
        return "estoque", "nome do arquivo"
    if "vendas" in filename_key or "venda" in filename_key:
        return "vendas", "nome do arquivo"

    header_keys = {_normalize(header) for header in headers}
    stock_signals = {"estoque", "giro mensal", "custo medio"}
    sales_signals = {"periodo", "quantidade vendida", "valor vendido"}
    stock_score = len(header_keys & stock_signals)
    sales_score = len(header_keys & sales_signals)
    if stock_score > sales_score and stock_score > 0:
        return "estoque", "estrutura dos cabeçalhos"
    if sales_score > stock_score and sales_score > 0:
        return "vendas", "estrutura dos cabeçalhos"
    return None, "tipo inconclusivo"


def _detect_csv_separator(content: bytes) -> str:
    sample = content[:8192].decode("utf-8-sig", errors="replace")
    try:
        return csv.Sniffer().sniff(sample, delimiters=";,\t|").delimiter
    except csv.Error:
        return ";"


def process_uploaded_file(
    file_name: str,
    file_bytes: bytes,
    report_type: str,
    approved_mapping: dict[str, str],
) -> dict[str, object]:
    """Aplica um mapeamento revisado e gera o modelo de saída em memória."""
    started_at = perf_counter()
    config = REPORT_CONFIGS[report_type]
    template_path = _resolve_template(report_type)
    _validate_template(template_path, report_type)
    suffix = Path(file_name).suffix.casefold()
    if suffix not in {".xlsx", ".xls", ".xlsm", ".csv"}:
        raise ValueError("Use um arquivo .xlsx, .xls, .xlsm ou .csv.")

    canonical_sources = {canonical: source for source, canonical in approved_mapping.items()}
    missing_required = REQUIRED_FIELDS - set(canonical_sources)
    if missing_required:
        missing_names = ", ".join(FIELD_LABELS[field] for field in sorted(missing_required))
        raise ValueError(f"Mapeie os campos obrigatórios antes de processar: {missing_names}.")
    if len(canonical_sources) != len(approved_mapping):
        raise ValueError("Uma coluna de origem foi associada a mais de um campo do modelo.")

    dtype = {
        source: "string"
        for source, canonical in approved_mapping.items()
        if canonical in {"ean", "cnpj", "unidade", "cod_reduzido"}
    }

    with TemporaryDirectory(prefix="data_intelligence_") as temporary_directory:
        temporary_root = Path(temporary_directory)
        source_path = temporary_root / f"entrada{suffix}"
        source_path.write_bytes(file_bytes)
        if suffix == ".csv":
            source_dataset = read_csv(
                source_path,
                sep=_detect_csv_separator(file_bytes),
                dtype=dtype,
                usecols=tuple(approved_mapping),
            )
        else:
            source_dataset = read_excel(
                source_path,
                dtype=dtype,
                usecols=tuple(approved_mapping),
            )

        input_rows = source_dataset.row_count
        source_frame = source_dataset.data
        missing_sources = set(approved_mapping) - set(source_frame.columns)
        if missing_sources:
            raise ValueError(
                "Colunas selecionadas não foram encontradas no arquivo: "
                + ", ".join(sorted(missing_sources))
            )
        source_frame = source_frame.loc[:, list(approved_mapping)].copy()
        source_dataset = Dataset(
            data=source_frame,
            source=source_dataset.source,
            source_format=source_dataset.source_format,
        )
        text_fields = {
            "cnpj", "unidade", "mes", "ean", "cod_reduzido",
            "descricao_produto", "grupo", "subgrupo", "laboratorio",
        }
        for source, canonical in approved_mapping.items():
            if canonical in text_fields and (
                pd.api.types.is_object_dtype(source_frame[source].dtype)
                or pd.api.types.is_string_dtype(source_frame[source].dtype)
            ):
                source_frame[source] = source_frame[source].astype("string").str.strip()

        prepared_dataset = prepare_dataset(
            source_dataset,
            drop_empty_rows=True,
            require_value_columns=(
                canonical_sources["ean"],
                canonical_sources["descricao_produto"],
            ),
        )
        if prepared_dataset.row_count == 0:
            raise ValueError("Nenhuma linha possui EAN e descrição preenchidos. Não há dados para exportar.")
        canonical_dataset = apply_column_mapping(prepared_dataset, approved_mapping)

        output_path = temporary_root / f"DADOS_TRATADOS_{report_type.upper()}.xlsx"
        canonical_frame = canonical_dataset.data
        mapped_fields = set(approved_mapping.values())
        export_frame = pd.DataFrame(index=canonical_frame.index)
        for field in config["fields"]:
            if field in mapped_fields and field in canonical_frame.columns:
                export_frame[field] = canonical_frame[field]
            else:
                export_frame[field] = pd.NA
        export_dataset = Dataset(
            data=export_frame,
            source=canonical_dataset.source,
            source_format=canonical_dataset.source_format,
        )
        write_excel_template(
            export_dataset,
            template_path=template_path,
            output_path=output_path,
            sheet_name=str(config["sheet_name"]),
        )
        output_bytes = output_path.read_bytes()

    expected_columns = [FIELD_LABELS[field] for field in config["fields"]]
    output_frame = export_frame.rename(columns=FIELD_LABELS)
    output_frame = output_frame[expected_columns].reset_index(drop=True)
    output_columns = {_normalize(column): column for column in output_frame.columns}
    for required_field in REQUIRED_FIELDS:
        column_name = output_columns[_normalize(FIELD_LABELS[required_field])]
        values = output_frame[column_name].astype("string").str.strip()
        if values.isna().any() or values.eq("").any():
            raise RuntimeError(
                f"A exportação contém {FIELD_LABELS[required_field]} vazio. O arquivo foi bloqueado."
            )
    return {
        "name": file_name,
        "report_type": report_type,
        "output_name": f"DADOS_TRATADOS_{report_type.upper()}.xlsx",
        "output_bytes": output_bytes,
        "frame": output_frame,
        "input_rows": input_rows,
        "output_rows": len(output_frame),
        "removed_rows": input_rows - prepared_dataset.row_count,
        "elapsed_seconds": round(perf_counter() - started_at, 2),
        "unmapped_fields": [
            FIELD_LABELS[field]
            for field in config["fields"]
            if field not in mapped_fields
        ],
    }


def _style_page() -> None:
    st.markdown(
        """
        <style>
        .stApp { background: #f3f7f8; }
        [data-testid="stHeader"] { background: rgba(243,247,248,.92); }
        .block-container { padding-top: 1.4rem; max-width: 1120px; }
        .hero { padding: 1.3rem 1.5rem; border-radius: 14px;
                color: white; background: linear-gradient(120deg,#12394b,#167d83);
                margin-bottom: 1rem; }
        .hero h1 { font-size: 1.8rem; margin: .1rem 0 .35rem 0; color: white; }
        .hero p { color: #d7eeee; margin: 0; font-size: .98rem; }
        .step-card { padding: 1rem 1.2rem; border: 1px solid #dce6e9;
                     background: white; border-radius: 11px; min-height: 90px; }
        .step-card strong { color: #167d83; }
        .wizard { display:flex; align-items:center; gap:.55rem; margin: 1.1rem 0 1.4rem; }
        .wizard-step { color:#657783; font-size:.82rem; white-space:nowrap; }
        .wizard-step span { display:inline-grid; place-items:center; width:1.65rem; height:1.65rem;
          margin-right:.35rem; border:1px solid #dce6e9; border-radius:50%; background:white; }
        .wizard-step.current { color:#167d83; font-weight:650; }
        .wizard-step.current span,.wizard-step.done span { color:white; background:#167d83; border-color:#167d83; }
        .wizard-line { height:1px; background:#dce6e9; flex:1; }
        div[data-testid="stMetric"] { background: white; padding: .8rem 1rem;
          border: 1px solid #dce6e9; border-radius: 11px; }
        div.stButton > button[kind="primary"] { background: #167d83; border-color: #167d83; }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _inspect_upload(file_name: str, file_bytes: bytes) -> tuple[str | None, str, list[str]]:
    if Path(file_name).suffix.casefold() == ".csv":
        frame = pd.read_csv(BytesIO(file_bytes), sep=None, engine="python", nrows=0)
    else:
        frame = pd.read_excel(BytesIO(file_bytes), nrows=0)
    columns = [str(column) for column in frame.columns]
    report_type, reason = detect_report_type(file_name, columns)
    return report_type, reason, columns


def _render_stepper(active_step: int) -> None:
    labels = ["Enviar arquivos", "Identificar", "Revisar", "Baixar"]
    parts = ['<div class="wizard">']
    for index, label in enumerate(labels, start=1):
        state = "current" if index == active_step else "done" if index < active_step else ""
        parts.append(
            f'<div class="wizard-step {state}"><span>{index if index >= active_step else "✓"}</span>{label}</div>'
        )
        if index < len(labels):
            parts.append('<div class="wizard-line"></div>')
    parts.append("</div>")
    st.markdown("".join(parts), unsafe_allow_html=True)


def _go_to_step(step: int) -> None:
    st.session_state["workflow_step"] = step
    st.rerun()


def _render_navigation(previous_step: int | None, next_label: str, *, disabled: bool = False) -> bool:
    back_column, spacer, next_column = st.columns([1, 5, 1.6])
    if previous_step is not None:
        if back_column.button("← Voltar", use_container_width=True):
            _go_to_step(previous_step)
    return next_column.button(
        next_label,
        type="primary",
        disabled=disabled,
        use_container_width=True,
    )


def main() -> None:
    st.set_page_config(
        page_title="Data Intelligence | Processamento guiado",
        page_icon="📊",
        layout="wide",
    )
    _style_page()

    if "workflow_step" not in st.session_state:
        st.session_state["workflow_step"] = 1
    step = int(st.session_state["workflow_step"])

    st.markdown(
        """
        <section class="hero">
          <h1>Data Intelligence</h1>
          <p>Prepare relatórios de estoque e vendas em quatro etapas simples.</p>
        </section>
        """,
        unsafe_allow_html=True,
    )
    st.caption(
        "Aplicativo local. Os arquivos de entrada são processados nesta máquina e não são enviados ao banco de dados."
    )
    _render_stepper(step)

    if step == 1:
        st.header("1. Envie os arquivos")
        st.write("Selecione relatórios de estoque e/ou vendas. Os arquivos ficam no processamento local desta sessão.")
        left, right = st.columns([1.5, 0.8], gap="large")
        with left:
            uploads = st.file_uploader(
                "Solte os arquivos nesta área ou selecione do computador",
                type=["xlsx", "xls", "xlsm", "csv"],
                accept_multiple_files=True,
                help="Para a demonstração, use TESTEML_ESTOQUE.xlsx e TESTEML_VENDAS.xlsx.",
                key="guided_uploads",
            )
            st.caption("Formatos aceitos: .xls, .xlsx, .xlsm e .csv")
        with right:
            st.markdown(
                """
                <div class="step-card">
                  <strong>Modelos de destino</strong><br/>
                  Estoque e vendas<br/><br/>
                  <strong>Obrigatórios</strong><br/>
                  EAN e descrição do produto<br/><br/>
                  <span style="color:#657783">Os demais campos sem origem permanecem vazios.</span>
                </div>
                """,
                unsafe_allow_html=True,
            )
            local_models_ready = True
            for report_type in REPORT_CONFIGS:
                try:
                    _validate_template(_resolve_template(report_type), report_type)
                except Exception:
                    local_models_ready = False
            if local_models_ready:
                st.success("Os modelos locais de estoque e vendas foram encontrados.")
            else:
                st.warning(
                    "Não encontrei os dois modelos exatos na pasta configurada. "
                    "A saída ficará bloqueada até localizar os arquivos corretos."
                )
        if uploads:
            st.write(f"**{len(uploads)} arquivo(s) selecionado(s)**")
            for uploaded in uploads:
                st.write(f"• {uploaded.name} · {uploaded.size:,} bytes")
        if _render_navigation(None, "Continuar para identificação →", disabled=not uploads):
            descriptions: list[dict[str, object]] = []
            for uploaded in uploads:
                file_bytes = uploaded.getvalue()
                try:
                    report_type, reason, columns = _inspect_upload(uploaded.name, file_bytes)
                    error = None
                except Exception as exc:
                    report_type, reason, columns, error = None, "arquivo não pôde ser lido", [], str(exc)
                descriptions.append(
                    {
                        "name": uploaded.name,
                        "bytes": file_bytes,
                        "report_type": report_type,
                        "reason": reason,
                        "columns": columns,
                        "error": error,
                    }
                )
            st.session_state["identified_files"] = descriptions
            st.session_state["processed_files"] = []
            st.session_state["processing_errors"] = []
            _go_to_step(2)

    elif step == 2:
        st.header("2. Confira a identificação")
        st.write("Confirme o tipo e revise como as colunas de origem serão associadas ao modelo final.")
        identified_files = st.session_state.get("identified_files", [])
        if not identified_files:
            st.warning("Não há arquivos nesta etapa. Volte e selecione os relatórios.")
            if st.button("Voltar ao envio"):
                _go_to_step(1)
            return

        for index, item in enumerate(identified_files):
            with st.container(border=True):
                file_col, evidence_col = st.columns([1.1, 1])
                file_col.markdown(f"**{item['name']}**")
                if item["error"]:
                    file_col.error(f"Arquivo não lido: {item['error']}")
                else:
                    file_col.caption(f"Sugestão: {item['report_type'] or 'inconclusiva'} · evidência: {item['reason']}")
                options = ["estoque", "vendas"]
                current = item["report_type"] if item["report_type"] in options else None
                selected = evidence_col.selectbox(
                    "Tipo do relatório",
                    options,
                    index=options.index(current) if current else None,
                    placeholder="Selecione estoque ou vendas",
                    key=f"report_type_{index}",
                )
                item["confirmed_report_type"] = selected

                if selected:
                    config = REPORT_CONFIGS[selected]
                    with st.expander("Revisar campos do modelo", expanded=True):
                        columns = item["columns"]
                        duplicate_headers = sorted(
                            {column for column in columns if columns.count(column) > 1}
                        )
                        if duplicate_headers:
                            st.error(
                                "O arquivo tem cabeçalhos repetidos e precisa ser corrigido antes do mapeamento: "
                                + ", ".join(duplicate_headers)
                            )
                        suggested_mapping = _suggest_field_mapping(columns, selected)
                        suggested_by_field = {
                            canonical: source
                            for source, canonical in suggested_mapping.items()
                        }
                        selections: dict[str, str | None] = {}
                        field_columns = st.columns(2)
                        for field_index, canonical_field in enumerate(config["fields"]):
                            label = FIELD_LABELS[canonical_field]
                            current_source = suggested_by_field.get(canonical_field)
                            choices: list[str | None] = [None, *columns]
                            current_index = choices.index(current_source) if current_source in choices else 0
                            selections[canonical_field] = field_columns[field_index % 2].selectbox(
                                label,
                                choices,
                                index=current_index,
                                format_func=lambda value: "— deixar vazio —" if value is None else value,
                                key=f"field_{index}_{selected}_{canonical_field}",
                                help=(
                                    "Obrigatório para cada linha."
                                    if canonical_field in REQUIRED_FIELDS
                                    else "Opcional. Se não mapear uma coluna, este campo ficará vazio."
                                ),
                            )

                        used_sources = [source for source in selections.values() if source]
                        duplicate_sources = sorted(
                            {source for source in used_sources if used_sources.count(source) > 1}
                        )
                        approved_mapping = {
                            str(source): canonical_field
                            for canonical_field, source in selections.items()
                            if source
                        }
                        item["approved_mapping"] = approved_mapping
                        missing_required = [
                            FIELD_LABELS[field]
                            for field in REQUIRED_FIELDS
                            if not selections.get(field)
                        ]
                        if missing_required:
                            st.error("Associe uma coluna de origem a: " + ", ".join(missing_required) + ".")
                        if duplicate_sources:
                            st.error("Cada coluna de origem pode preencher apenas um campo. Revise: " + ", ".join(duplicate_sources))
                        optional_blank = [
                            FIELD_LABELS[field]
                            for field in config["fields"]
                            if field not in REQUIRED_FIELDS and not selections.get(field)
                        ]
                        if optional_blank:
                            st.caption("Campos que sairão vazios: " + ", ".join(optional_blank))
                        item["mapping_is_valid"] = not missing_required and not duplicate_sources
                        if duplicate_headers:
                            item["mapping_is_valid"] = False

        has_unreadable = any(item["error"] for item in identified_files)
        has_unselected = any(not item.get("confirmed_report_type") for item in identified_files)
        has_invalid_mapping = any(not item.get("mapping_is_valid", False) for item in identified_files)
        if has_unreadable:
            st.warning("Remova ou corrija os arquivos que não puderam ser lidos antes de continuar.")
        if _render_navigation(1, "Confirmar e continuar →", disabled=has_unreadable or has_unselected or has_invalid_mapping):
            st.session_state["identified_files"] = identified_files
            _go_to_step(3)

    elif step == 3:
        st.header("3. Revise o resultado")
        st.write("Confira as linhas de saída e os avisos. A origem não é alterada.")
        identified_files = st.session_state.get("identified_files", [])
        processed_files = st.session_state.get("processed_files", [])
        if not processed_files:
            st.info("Revise os tipos confirmados e execute o tratamento do perfil sintético.")
            if st.button("Executar tratamento", type="primary", disabled=not identified_files):
                processed: list[dict[str, object]] = []
                errors: list[str] = []
                progress = st.progress(0, text="Iniciando tratamento...")
                for index, item in enumerate(identified_files):
                    try:
                        processed.append(
                            process_uploaded_file(
                                str(item["name"]),
                                item["bytes"],
                                str(item["confirmed_report_type"]),
                                dict(item["approved_mapping"]),
                            )
                        )
                    except Exception as exc:
                        errors.append(f"{item['name']}: {exc}")
                    progress.progress(
                        (index + 1) / len(identified_files),
                        text=f"Processados {index + 1} de {len(identified_files)} arquivo(s)",
                    )
                st.session_state["processed_files"] = processed
                st.session_state["processing_errors"] = errors
                st.rerun()
            return

        for error in st.session_state.get("processing_errors", []):
            st.error(error)
        if not processed_files:
            st.warning("Nenhum arquivo foi processado. Volte e corrija as entradas.")
            if st.button("Voltar à identificação"):
                _go_to_step(2)
            return

        for result in processed_files:
            st.subheader(f"{result['name']} · {str(result['report_type']).title()}")
            metric_columns = st.columns(4)
            metric_columns[0].metric("Linhas recebidas", result["input_rows"])
            metric_columns[1].metric("Linhas na saída", result["output_rows"])
            metric_columns[2].metric("Removidas (EAN/descrição)", result["removed_rows"])
            metric_columns[3].metric("Tempo de tratamento", f"{result['elapsed_seconds']:.2f} s")
            if result["unmapped_fields"]:
                st.info(
                    "Campos sem coluna de origem, exportados vazios: "
                    + ", ".join(result["unmapped_fields"])
                )
            st.dataframe(result["frame"].head(100), hide_index=True, use_container_width=True)
            st.caption(f"Prévia das primeiras 100 linhas de {result['output_rows']}.")
            st.divider()

        if _render_navigation(
            2,
            "Resultado revisado · ir para downloads →",
            disabled=bool(st.session_state.get("processing_errors")),
        ):
            _go_to_step(4)

    else:
        st.header("4. Baixe os arquivos tratados")
        st.write("Os arquivos abaixo seguem os modelos sintéticos configurados e podem ser conferidos antes do uso.")
        processed_files = st.session_state.get("processed_files", [])
        if not processed_files:
            st.warning("Ainda não há resultados para baixar. Comece pelo envio dos arquivos.")
            if st.button("Iniciar novo processamento"):
                _go_to_step(1)
            return
        for result in processed_files:
            with st.container(border=True):
                file_col, download_col = st.columns([2, 1])
                file_col.markdown(f"**{result['output_name']}**")
                file_col.caption(
                    f"{result['output_rows']:,} linhas · relatório de {result['report_type']} · arquivo Excel"
                )
                download_col.download_button(
                    "Baixar XLSX",
                    data=result["output_bytes"],
                    file_name=result["output_name"],
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    key=f"download_{result['report_type']}_{result['name']}",
                    type="primary",
                    use_container_width=True,
                )
        st.divider()
        if st.button("＋ Iniciar novo processamento"):
            for key in ("identified_files", "processed_files", "processing_errors"):
                st.session_state.pop(key, None)
            st.session_state.pop("guided_uploads", None)
            st.session_state["workflow_step"] = 1
            st.rerun()

        if st.button("← Voltar à revisão"):
            _go_to_step(3)


if __name__ == "__main__":
    main()
