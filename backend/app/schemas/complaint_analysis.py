"""客诉分析的 Pydantic Schema。

字段与 ``analysis_result`` 表一一对应，枚举值来自
``客诉标签分类_整理版.xlsx``。Instructor 会用本 Schema 约束并校验
Xiaomi MiMo 的结构化输出。
"""
from typing import Literal

from pydantic import BaseModel, Field, model_validator


FUNCTION_TAGS = {
    "C1": {"不加热", "不转动", "不出雾", "按键失灵", "屏不亮"},
    "C2": {"粉碎不细", "加热慢", "温控不准", "出汁少", "噪音大"},
    "C3": {"漏水", "异响", "自动断电", "糊底", "开裂"},
    "C4": {"漏电", "冒烟", "烫伤", "起火", "异味刺鼻"},
    "C5": {"掉漆", "生锈", "毛刺", "接缝不严", "材质薄"},
    "C6": {"难清洗", "说明不清", "操作复杂", "容量虚标"},
    "C7": {"不理人", "维修慢", "推诿", "收费乱"},
    "C8": {"破损", "漏发", "包装简陋", "送货慢"},
    "C9": {"功效夸大", "参数不符", "赠品缺失"},
    "C10": {"使用咨询", "功能建议", "好评"},
}

PRODUCTION_STAGES = {
    "设计研发": {"产品定义", "结构设计", "电路设计"},
    "原材料": {"玻璃", "不锈钢", "塑料", "涂层", "电机", "电子元器件"},
    "生产制造": {"组装", "焊接", "注塑", "喷涂", "贴片"},
    "质量检测": {"来料检验", "过程检", "成品检", "老化测试"},
    "包装运输": {"包装防护", "物流装卸", "快递暴力"},
    "仓储配送": {"仓库发货", "库存积压", "错发漏发"},
    "安装调试": {"首次使用指导", "装配复杂度"},
    "购买咨询": {"效果咨询", "功能咨询", "操作咨询", "其他咨询"},
}

PARTS = {
    "结构壳体": {"上盖 / 下壳", "机身外壳", "底座", "把手/提手", "装饰面板"},
    "动力系统": {"电机", "齿轮组/减速箱", "传动轴/联轴器", "风叶（风扇类）"},
    "加热系统": {"发热盘（壶/锅类）", "发热管（烤箱/炸锅）", "PTC 发热体（取暖/暖风）", "加热片"},
    "控制与电路": {"主控 PCB", "电源板/开关电源", "按键板/触控面板", "显示屏", "旋钮/按键"},
    "传感与保护": {"温控器（双金属片/NTC）", "温度探头", "防干烧开关", "温度保险丝", "微动/限位开关"},
    "容器内胆": {"杯体（破壁/料理）", "内胆/锅体（炖锅/饭煲）", "壶身（养生壶/水壶）", "水箱（加湿/咖啡机）"},
    "密封与紧固": {"密封圈/密封垫", "螺丝/铆钉", "卡扣/卡环", "减震胶垫"},
    "线束与电源": {"电源线", "插头", "内部线束/接插件", "电池包", "充电底座"},
    "功能执行件": {"刀片/刀头", "滤网/滤篮", "磨盘", "搅拌棒", "蒸架/蒸笼", "雾化片（加湿器）", "喷嘴"},
    "附件": {"刷头", "量杯", "适配器", "清洁刷", "配件包"},
}

FUNCTION_TAG_TO_CODE = {
    tag: code for code, tags in FUNCTION_TAGS.items() for tag in tags
}
SUBSTAGE_TO_STAGE = {
    substage: stage for stage, substages in PRODUCTION_STAGES.items() for substage in substages
}
PART_TO_CATEGORY = {
    part: category for category, parts in PARTS.items() for part in parts
}

FunctionCode = Literal["C1", "C2", "C3", "C4", "C5", "C6", "C7", "C8", "C9", "C10"]
FunctionTag = Literal[
    "不加热", "不转动", "不出雾", "按键失灵", "屏不亮", "粉碎不细", "加热慢", "温控不准",
    "出汁少", "噪音大", "漏水", "异响", "自动断电", "糊底", "开裂", "漏电", "冒烟", "烫伤",
    "起火", "异味刺鼻", "掉漆", "生锈", "毛刺", "接缝不严", "材质薄", "难清洗", "说明不清",
    "操作复杂", "容量虚标", "不理人", "维修慢", "推诿", "收费乱", "破损", "漏发", "包装简陋",
    "送货慢", "功效夸大", "参数不符", "赠品缺失", "使用咨询", "功能建议", "好评",
]
ProductionStage = Literal["设计研发", "原材料", "生产制造", "质量检测", "包装运输", "仓储配送", "安装调试", "购买咨询"]
ProductionSubstage = Literal[
    "产品定义", "结构设计", "电路设计", "玻璃", "不锈钢", "塑料", "涂层", "电机", "电子元器件",
    "组装", "焊接", "注塑", "喷涂", "贴片", "来料检验", "过程检", "成品检", "老化测试",
    "包装防护", "物流装卸", "快递暴力", "仓库发货", "库存积压", "错发漏发", "首次使用指导", "装配复杂度",
    "效果咨询", "功能咨询", "操作咨询", "其他咨询",
]
PartCategory = Literal[
    "结构壳体", "动力系统", "加热系统", "控制与电路", "传感与保护", "容器内胆", "密封与紧固",
    "线束与电源", "功能执行件", "附件",
]
PartName = Literal[
    "上盖 / 下壳", "机身外壳", "底座", "把手/提手", "装饰面板", "电机", "齿轮组/减速箱",
    "传动轴/联轴器", "风叶（风扇类）", "发热盘（壶/锅类）", "发热管（烤箱/炸锅）",
    "PTC 发热体（取暖/暖风）", "加热片", "主控 PCB", "电源板/开关电源", "按键板/触控面板",
    "显示屏", "旋钮/按键", "温控器（双金属片/NTC）", "温度探头", "防干烧开关", "温度保险丝",
    "微动/限位开关", "杯体（破壁/料理）", "内胆/锅体（炖锅/饭煲）", "壶身（养生壶/水壶）",
    "水箱（加湿/咖啡机）", "密封圈/密封垫", "螺丝/铆钉", "卡扣/卡环", "减震胶垫", "电源线",
    "插头", "内部线束/接插件", "电池包", "充电底座", "刀片/刀头", "滤网/滤篮", "磨盘", "搅拌棒",
    "蒸架/蒸笼", "雾化片（加湿器）", "喷嘴", "刷头", "量杯", "适配器", "清洁刷", "配件包",
]


class ComplaintAnalysis(BaseModel):
    """单条客户原声的标准化客诉标签结果。无法从原文判断的可选字段应留空。"""

    function_tag_l1: FunctionCode = Field(description="功能一级标签编码 C1-C10，只选最主要的一类")
    function_tag_l2: list[FunctionTag] = Field(min_length=1, description="对应一级标签的功能二级子标签，可多选")
    production_stage: ProductionStage | None = Field(default=None, description="可归因时选择生产一级环节")
    production_substage: ProductionSubstage | None = Field(default=None, description="必须与生产一级环节匹配")
    part_category: list[PartCategory] = Field(default_factory=list, description="原文明确或可可靠推断的部件大类")
    part_name: list[PartName] = Field(default_factory=list, description="原文明确或可可靠推断的具体部件")
    evaluation_level: Literal["好评", "中评", "差评", "疑问", "无意义"] = Field(
        description="评价等级，只能选择好评、中评、差评、疑问、无意义"
    )
    emotion_dimension: Literal["快乐", "悲伤", "愤怒", "恐惧", "厌恶"] = Field(
        description="这条评价的主要情绪五维，只能选择快乐、悲伤、愤怒、恐惧、厌恶"
    )
    problem_nature: Literal["质量缺陷", "功能不符", "体验不佳", "材质安全", "服务问题", "价格争议", "虚假宣传"]
    keyword_cluster: list[Literal[
        "耐用性", "材质安全", "温控问题", "噪音问题", "清洗问题", "容量问题", "操作问题", "售后问题", "颜值满意", "性价比"
    ]] = Field(default_factory=list, description="匹配的高频关键词簇，没有则为空数组")
    appeal_intent: Literal["退款", "换货", "维修", "补发", "道歉", "改进建议", "曝光维权"]

    @model_validator(mode="before")
    @classmethod
    def normalize_taxonomy_relations(cls, data):
        """将模型的合理但跨层级输出归一成 analysis_result 的单主类结构。

        JSON Schema 能展示字段枚举，却不能把 Python 校验器中的父子映射完整
        告诉模型。与其让同一条数据反复重试，这里以二级标签为事实来源，确定性
        修正父级并丢弃其他一级类下的次要标签。
        """
        if not isinstance(data, dict):
            return data
        normalized = dict(data)

        # 兼容 MiMo 自定义字段名 -> Schema 标准字段名
        alias_map = {
            "production_phase": "production_stage",
            "production_phase_detail": "production_substage",
            "component": "part_name",
            "component_category": "part_category",
            "fault_type": "problem_nature",
            "fault_description": "problem_nature",
            "appeal": "appeal_intent",
            "question": "appeal_intent",
        }
        for alias, standard in alias_map.items():
            if alias in normalized and standard not in normalized:
                normalized[standard] = normalized.get(alias)
            if alias in normalized:
                normalized.pop(alias, None)

        # 若 part_name 是字符串则归一为列表
        if isinstance(normalized.get("part_name"), str):
            normalized["part_name"] = [normalized["part_name"]] if normalized["part_name"] else []
        if isinstance(normalized.get("part_category"), str):
            normalized["part_category"] = [normalized["part_category"]] if normalized["part_category"] else []

        raw_tags = normalized.get("function_tag_l2") or []
        if isinstance(raw_tags, str):
            raw_tags = [raw_tags]
        known_tags = [tag for tag in raw_tags if tag in FUNCTION_TAG_TO_CODE]
        requested_code = normalized.get("function_tag_l1")
        matching_tags = [
            tag for tag in known_tags if FUNCTION_TAG_TO_CODE[tag] == requested_code
        ]
        if matching_tags:
            normalized["function_tag_l2"] = list(dict.fromkeys(matching_tags))
        elif known_tags:
            inferred_code = FUNCTION_TAG_TO_CODE[known_tags[0]]
            normalized["function_tag_l1"] = inferred_code
            normalized["function_tag_l2"] = list(
                dict.fromkeys(
                    tag for tag in known_tags if FUNCTION_TAG_TO_CODE[tag] == inferred_code
                )
            )

        substage = normalized.get("production_substage")
        if substage in SUBSTAGE_TO_STAGE:
            normalized["production_stage"] = SUBSTAGE_TO_STAGE[substage]
        elif not substage:
            normalized["production_stage"] = None
            normalized["production_substage"] = None

        raw_parts = normalized.get("part_name") or []
        if isinstance(raw_parts, str):
            raw_parts = [raw_parts]
        known_parts = [part for part in raw_parts if part in PART_TO_CATEGORY]
        if known_parts:
            normalized["part_name"] = list(dict.fromkeys(known_parts))
            normalized["part_category"] = list(
                dict.fromkeys(PART_TO_CATEGORY[part] for part in known_parts)
            )

        if normalized.get("appeal_intent") in {"咨询", "使用咨询", "功能咨询"}:
            normalized["appeal_intent"] = "改进建议"
        return normalized

    @model_validator(mode="after")
    def validate_taxonomy_relations(self):
        if not set(self.function_tag_l2).issubset(FUNCTION_TAGS[self.function_tag_l1]):
            raise ValueError("功能二级标签与一级编码不匹配")
        if (self.production_stage is None) != (self.production_substage is None):
            raise ValueError("生产一级环节和二级子环节必须同时为空或同时有值")
        if self.production_stage and self.production_substage not in PRODUCTION_STAGES[self.production_stage]:
            raise ValueError("生产二级子环节与一级环节不匹配")
        selected_parts = set().union(*(PARTS[name] for name in self.part_category)) if self.part_category else set()
        if not set(self.part_name).issubset(selected_parts):
            raise ValueError("具体部件与部件大类不匹配")
        return self
