REASONS = {
    'EMPTY': '文件无内容', 'BLANK_FILE': '文件只有空白', 'HEADER_ONLY': '文件只有表头',
    'ENCODING': '无法识别编码', 'CSV': '表格语法错误', 'HEADER': '表头无效',
    'WIDTH': '列数与表头不一致', 'CONTRACT': '列契约无法应用', 'REQUIRED': '主键或业务字段缺失',
    'TIMESTAMP': '时间需包含偏移量', 'NUMBER': '数字无法归一', 'RANGE': '数字越界',
    'EXACT_DUP': '同版本重复传输', 'SUPERSEDED': '已被更新版本代替',
    'REV_CONFLICT': '最高版本证据有冲突', 'BUSINESS': '业务规则无法判定',
    'MISSING_BOOK': '外部账缺少业务键', 'MISSING_RESULT': '复算结果缺少业务键',
    'AMOUNT_DELTA': '复算与外部账计量不同', 'BOOK_CONFLICT': '独立账含重复业务键',
    'ZERO_CLAIM': '前导零差异，按唯一对应认领', 'KEY_AMBIGUOUS': '卡号归属待裁判核实',
    'KEY_VERIFIED': '卡号归属已经裁判核清', 'KEY_DISMISSED': '外部账此笔不予认领',
    'CLAIM_PENDING': '卡号归属未核清，不能签核', 'CLAIM_UNKNOWN': '该笔外部账不在待核归属中',
    'CLAIM_CARD': '候选归属中无此计时卡', 'CLAIM_CONFLICT': '该计时卡已被其他外部账认领',
    'RUN_UNKNOWN': '没有此批次', 'DEMO_UNKNOWN': '没有此样例', 'STALE': '复核版本已过期',
    'REVIEW_NOTE': '有差异时须填写复核意见', 'REVIEW_DECISION': '复核结论无效',
}

REASONS.update({'RACE_CHAIN': '检查点配置无效', 'RACE_READER': '未知计时点', 'RACE_GAP': '未找到可接续读数', 'DATE': '日期格式无效', 'REV_BLOCKED': '较新来源尚未采信'})
