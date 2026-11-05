# /// script
# dependencies = [
#     "pandas",
#     "openpyxl",
# ]
# ///

from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
XLSX_PATH = ROOT / "teams" / "authors_info.xlsx"
TEX_PATH = ROOT / "authors.tex"
CREDIT_TEX_PATH = ROOT / "authors_credit.tex"
MARKDOWN_PATH = ROOT / "authors.md"

CORRESPONDING_TEAM = "TEAM00"


def format_author_block(row: pd.Series, corresponding: bool) -> str:
    initials = " ".join(f"{part[0]}." for part in row["Name"].split())
    full_name = f"{initials} {row['Surname']}"

    affiliations = [aff.strip() for aff in row["Affiliations"].split(";") if aff.strip()]

    lines = [f"\\author{{{full_name}}}"]
    if affiliations:
        lines.append(f"\\affiliation{{{affiliations[0]}}}")
        for aff in affiliations[1:]:
            lines.append(f"\\alsoaffiliation{{{aff}}}")

    if corresponding:
        lines.append(f"\\email[{full_name}]{{{row['email']}}}")

    return "\n".join(lines)


def format_author_markdown(row: pd.Series, affiliation_numbers: dict[str, int]) -> str:
    initials = " ".join(f"{part[0]}." for part in row["Name"].split())
    full_name = f"{initials} {row['Surname']}"
    affiliations = [aff.strip() for aff in row["Affiliations"].split(";") if aff.strip()]

    numbers = ",".join(str(affiliation_numbers[affiliation]) for affiliation in affiliations)
    marker = f"<sup>{numbers}</sup>" if numbers else ""
    return f"{full_name}{marker}"


def format_credit_taxonomy(df: pd.DataFrame) -> str:
    author_columns = {"Team ID", "Name", "Surname", "Affiliations", "ORCID", "email"}
    roles = sorted(set(df.columns) - author_columns, key=str.casefold)
    lines = []
    for role in roles:
        contributors = df[df[role].str.strip().str.casefold() == "true"]
        initials = [
            "".join(f"{part[0]}." for part in f"{row['Name']} {row['Surname']}".split())
            for _, row in contributors.iterrows()
        ]
        if initials:
            escaped_role = role.replace("&", r"\&")
            lines.append(f"{escaped_role}: {', '.join(initials)}")
    return "\n".join(lines) + ("\n" if lines else "") + "All the authors approved the final submitted draft.\n"


def main() -> None:
    df = pd.read_excel(XLSX_PATH, dtype=str).fillna("")
    df.columns = df.columns.str.strip()
    df["Team ID"] = df["Team ID"].str.strip()
    df["Name"] = df["Name"].str.strip()
    df["Surname"] = df["Surname"].str.strip()

    df = df[df["Team ID"] != ""]

    team00 = df[df["Team ID"] == CORRESPONDING_TEAM]
    others = df[df["Team ID"] != CORRESPONDING_TEAM].sort_values("Surname")

    ordered = pd.concat([team00, others], ignore_index=True)

    affiliation_numbers: dict[str, int] = {}
    for _, row in ordered.iterrows():
        affiliations = [aff.strip() for aff in row["Affiliations"].split(";") if aff.strip()]
        for affiliation in affiliations:
            affiliation_numbers.setdefault(affiliation, len(affiliation_numbers) + 1)

    blocks = [
        format_author_block(row, corresponding=(i == 0))
        for i, row in ordered.iterrows()
    ]
    markdown_authors = [
        format_author_markdown(row, affiliation_numbers)
        for _, row in ordered.iterrows()
    ]
    markdown_affiliations = [
        f"<sup>{number}</sup> {affiliation}"
        for affiliation, number in affiliation_numbers.items()
    ]

    TEX_PATH.write_text("\n".join(blocks) + "\n")
    CREDIT_TEX_PATH.write_text(format_credit_taxonomy(ordered))
    markdown = ", ".join(markdown_authors[:-1]) + " and " + markdown_authors[-1]
    markdown += "\n\n---\n\n" + "; ".join(markdown_affiliations[:-1]) + " and " + markdown_affiliations[-1] + "\n"
    MARKDOWN_PATH.write_text(markdown)


if __name__ == "__main__":
    main()
