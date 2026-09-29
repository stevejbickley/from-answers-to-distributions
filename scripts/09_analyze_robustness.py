import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import argparse
import json
from src.robustness import option_order_metrics


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--order', default='data/processed/option_order_robustness.jsonl')
    p.add_argument('--out', default='results/option_order_metrics.csv')
    a = p.parse_args()
    if not Path(a.order).exists():
        print('No option-order records found; skipped')
        return
    records = [json.loads(x) for x in Path(a.order).read_text().splitlines() if x.strip()]
    metrics, coverage = option_order_metrics(records)
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    metrics.to_csv(out, index=False)
    coverage.to_csv(out.with_name('option_order_coverage.csv'), index=False)
    print('Wrote', out, 'and option-order coverage audit')


if __name__ == '__main__':
    main()
