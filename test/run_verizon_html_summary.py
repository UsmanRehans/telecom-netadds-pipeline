import sys
import os
import pandas as pd

# Allow imports from same folder
sys.path.append(os.path.dirname(__file__))

from verizon_clean_scraper import build_summary_table_from_html, build_detailed_table_from_html


def main(html_path: str, out_csv: str):
    with open(html_path, 'r', encoding='utf-8') as f:
        html_content = f.read()

    summary_df = build_summary_table_from_html(html_content)
    print("\nSummary Table (in thousands):")
    print(summary_df.to_string(index=False))
    summary_df.to_csv(out_csv, index=False)
    print(f"\nSaved summary table to {out_csv}")

    # Also produce a detailed table with 2025/2024 for connections and net adds
    detailed_df = build_detailed_table_from_html(html_content)
    detailed_out = os.path.join(os.path.dirname(out_csv), 'verizon_detailed_table_from_file.csv')
    print("\nDetailed Table (in thousands):")
    print(detailed_df.to_string(index=False))
    detailed_df.to_csv(detailed_out, index=False)
    print(f"\nSaved detailed table to {detailed_out}")


if __name__ == "__main__":
    # Defaults to the saved Verizon file if no args provided
    default_html = os.path.join(os.path.dirname(__file__), '..', 'data', 'verizon_first_filing.html')
    default_out = os.path.join(os.path.dirname(__file__), '..', 'data', 'verizon_summary_table_from_file.csv')

    html_path = sys.argv[1] if len(sys.argv) > 1 else default_html
    out_csv = sys.argv[2] if len(sys.argv) > 2 else default_out

    main(html_path, out_csv)


