-- ============================================================
-- 原声分析平台：两张业务表
-- 表一 dataset_info    数据集需要提供的信息（含客户原文）
-- 表二 analysis_result 需要从对话中分析的信息
-- 多值标签（功能子标签/部件/关键词簇）使用 text[] 数组
-- ============================================================

CREATE TABLE IF NOT EXISTS dataset_info (
    id                  BIGSERIAL PRIMARY KEY,
    source_product_id   TEXT,                              -- 商品目录中的来源商品 ID
    -- 客户原文与来源渠道
    customer_transcript TEXT        NOT NULL,              -- 客户原文（按触点渠道提取的有效抱怨）
    touchpoint          TEXT        NOT NULL,              -- 触点渠道编码（S1~S5）
    source_form         TEXT,                              -- 原始形态（多轮对话流/评分+文本+图片等）
    -- 品类（SKU 级）
    category_l1         TEXT        NOT NULL,              -- 一级分类（厨电/生活小家电等）
    category_l2         TEXT        NOT NULL,              -- 二级分类（锅煲类/电热类等）
    category_l3         TEXT        NOT NULL,              -- 三级分类（电炖盅/养生壶等）
    sku                 TEXT        NOT NULL,              -- SKU 编码（如 DDH-208）
    -- 客户画像
    region              TEXT,                              -- 大区
    province            TEXT,                              -- 省份
    city_tier           TEXT,                              -- 城市线级
    gender              TEXT,                              -- 性别
    age                 TEXT,                              -- 年龄
    use_scene           TEXT,                              -- 使用场景
    user_type           TEXT,                              -- 用户类型（新客/老客/复购）
    member_level        TEXT,                              -- 会员等级
    -- 订单交易
    price_band          TEXT,                              -- 购买价格带
    paid_amount         NUMERIC(10,2),                     -- 实付金额
    original_amount     NUMERIC(10,2),                     -- 原价金额
    platform            TEXT        NOT NULL,              -- 购买平台
    promo_type          TEXT,                              -- 促销类型
    warranty_status     TEXT,                              -- 在保状态
    is_gift             BOOLEAN,                           -- 是否赠品
    complaint_time      TIMESTAMP,                         -- 投诉时点
    duration_to_complaint TEXT,                            -- 购买到投诉时长
    product_season      TEXT,                              -- 产品季节性
    complaint_season    TEXT,                              -- 投诉季节
    -- 生命周期
    lifecycle_stage     TEXT,                              -- 生命周期阶段
    -- 通用
    created_at          TIMESTAMP   NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS analysis_result (
    id                  BIGSERIAL PRIMARY KEY,
    dataset_info_id     BIGINT      NOT NULL
                        REFERENCES dataset_info(id)
                        ON DELETE CASCADE,                 -- 关联表一
    -- 功能标签
    function_tag_l1     TEXT        NOT NULL,              -- 功能一级标签（C1~C10）
    function_tag_l2     TEXT[],                            -- 功能二级子标签（可多选）
    -- 生产环节 / 产品部件
    production_stage    TEXT,                              -- 生产一级环节
    production_substage TEXT,                              -- 生产二级子环节
    part_category       TEXT[],                            -- 部件大类（可多选）
    part_name           TEXT[],                            -- 具体部件（可多选）
    -- 语义分析
    evaluation_level    TEXT        NOT NULL,              -- 评价等级：好评/中评/差评/疑问/无意义
    emotion_dimension   TEXT        NOT NULL,              -- 情绪五维：快乐/悲伤/愤怒/恐惧/厌恶
    problem_nature      TEXT        NOT NULL,              -- 问题性质
    keyword_cluster     TEXT[],                            -- 高频关键词簇（可多选）
    appeal_intent       TEXT        NOT NULL,              -- 诉求意图
    -- 通用
    created_at          TIMESTAMP   NOT NULL DEFAULT now()
);

-- 常用索引
CREATE INDEX IF NOT EXISTS idx_dataset_info_sku    ON dataset_info (sku);
CREATE INDEX IF NOT EXISTS idx_dataset_info_touch  ON dataset_info (touchpoint);
CREATE INDEX IF NOT EXISTS idx_analysis_result_di  ON analysis_result (dataset_info_id);
