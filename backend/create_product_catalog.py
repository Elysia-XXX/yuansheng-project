"""创建独立 product_catalog 数据库并导入商品参数目录。

用法：python create_product_catalog.py "D:\\...\\shop_params(1).xlsx"
"""
from __future__ import annotations

import json
import sys

import psycopg2
from psycopg2 import sql

from app.config import Config
from app.services.product_catalog import read_product_workbook


CATALOG_DB = Config.CATALOG_DB_NAME


DDL = """
CREATE TABLE IF NOT EXISTS product_catalog (
    id BIGSERIAL PRIMARY KEY,
    source_product_id TEXT NOT NULL UNIQUE,
    source_sheet TEXT NOT NULL,
    source_url TEXT,
    sku TEXT NOT NULL,
    category_l1 TEXT NOT NULL,
    category_l2 TEXT NOT NULL,
    category_l3 TEXT NOT NULL,
    classification_confidence NUMERIC(4,3) NOT NULL,
    classification_rule TEXT NOT NULL,
    raw_params JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_product_catalog_sku ON product_catalog (sku);
CREATE INDEX IF NOT EXISTS idx_product_catalog_category ON product_catalog (category_l1, category_l2, category_l3);
"""


def connect(dbname: str):
    return psycopg2.connect(
        host=Config.DB_HOST,
        port=Config.DB_PORT,
        user=Config.DB_USER,
        password=Config.DB_PASSWORD,
        dbname=dbname,
    )


def ensure_database() -> None:
    conn = connect(Config.DB_NAME)
    conn.autocommit = True
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (CATALOG_DB,))
            if cur.fetchone() is None:
                cur.execute(sql.SQL("CREATE DATABASE {} ").format(sql.Identifier(CATALOG_DB)))
                print(f"created database: {CATALOG_DB}")
            else:
                print(f"database exists: {CATALOG_DB}")
    finally:
        conn.close()


def import_products(path: str) -> int:
    products = read_product_workbook(path)
    conn = connect(CATALOG_DB)
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(DDL)
                for product in products:
                    cur.execute(
                        """
                        INSERT INTO product_catalog
                          (source_product_id, source_sheet, source_url, sku,
                           category_l1, category_l2, category_l3,
                           classification_confidence, classification_rule, raw_params)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb)
                        ON CONFLICT (source_product_id) DO UPDATE SET
                          source_sheet=EXCLUDED.source_sheet,
                          source_url=EXCLUDED.source_url,
                          sku=EXCLUDED.sku,
                          category_l1=EXCLUDED.category_l1,
                          category_l2=EXCLUDED.category_l2,
                          category_l3=EXCLUDED.category_l3,
                          classification_confidence=EXCLUDED.classification_confidence,
                          classification_rule=EXCLUDED.classification_rule,
                          raw_params=EXCLUDED.raw_params,
                          updated_at=now()
                        """,
                        (
                            product["source_product_id"],
                            product["source_sheet"],
                            product["source_url"],
                            product["sku"],
                            product["category_l1"],
                            product["category_l2"],
                            product["category_l3"],
                            product["confidence"],
                            product["classification_rule"],
                            json.dumps(product["raw_params"], ensure_ascii=False),
                        ),
                    )
    finally:
        conn.close()
    return len(products)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("用法：python create_product_catalog.py <shop_params.xlsx>")
    ensure_database()
    count = import_products(sys.argv[1])
    print(f"imported products: {count}")
