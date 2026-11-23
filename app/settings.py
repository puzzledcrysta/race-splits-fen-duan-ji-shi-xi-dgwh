import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SAMPLE_ROOT = ROOT / 'sample_data'
DB = Path(os.getenv('WORKBENCH_DB', str(ROOT/'state/ledger.sqlite3')))
TITLE = '分段计时席'
SLUG = 'race-splits'
KEY = '计时卡'
FIELDS = ('检查点链', '读数')
ROLE = '路跑赛事计时裁判'
UNIT = '秒'
RULE_VERSION = 'race-splits-1.0'
SIGNATURE = '计时点证据'
TABS = {'intake': '芯片读数', 'contract': '计时点约定', 'quality': '异常计时卡', 'domain': '分段择链', 'reconcile': '成绩核对', 'runs': '计时批次', 'review': '裁判签核'}
