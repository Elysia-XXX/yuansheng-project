# -*- coding: utf-8 -*-
"""对 dataset_info 中 S4（问大家）记录调用 MiMo 分析，映射到 analysis_result 表。

用法：
    python analyze_shop_qa.py [limit]
        limit 可选，默认分析全部无 analysis_result 的 S4 记录。
幂等：仅分析尚未生成 analysis_result 的记录，重复运行不重复打标。
"""
import sys
import time

from sqlalchemy import exists

from app import create_app
from app.db import db
from app.models import AnalysisResult, DatasetInfo
from app.services.complaint_analyzer import analyze_dataset_info


def main():
    limit_arg = sys.argv[1] if len(sys.argv) > 1 else None
    limit = None
    if limit_arg is not None:
        limit = int(limit_arg)
        if limit < 1:
            raise SystemExit("limit 必须是正整数")

    app = create_app()
    with app.app_context():
        pending_query = (
            DatasetInfo.query
            .filter(
                DatasetInfo.touchpoint == "S4",
                ~exists().where(AnalysisResult.dataset_info_id == DatasetInfo.id),
            )
            .order_by(DatasetInfo.id)
        )
        total_pending = pending_query.count()
        pending = pending_query.limit(limit).all() if limit else pending_query.all()
        print(f"待分析 S4 记录：{total_pending}，本次处理：{len(pending)}")

        analyzed = 0
        failed = 0
        errors = []
        started = time.time()
        for index, item in enumerate(pending, start=1):
            try:
                structured = analyze_dataset_info(item)
                db.session.add(
                    AnalysisResult(dataset_info_id=item.id, **structured.model_dump())
                )
                db.session.commit()
                analyzed += 1
            except Exception as exc:  # noqa: BLE001 - 单条失败不应中断整个批次
                db.session.rollback()
                current = str(exc).strip() or exc.__class__.__name__
                errors.append({"dataset_info_id": item.id, "error": current[:500]})
                failed += 1
            if index % 10 == 0 or index == len(pending):
                elapsed = time.time() - started
                print(
                    f"进度 {index}/{len(pending)} 成功 {analyzed} 失败 {failed} "
                    f"耗时 {elapsed:.0f}s"
                )

        remaining = pending_query.count()
        print("=" * 40)
        print(f"完成：请求 {len(pending)} 成功 {analyzed} 失败 {failed} 剩余 {remaining}")
        if errors:
            print("失败明细：")
            for err in errors:
                print(f"  dataset_info_id={err['dataset_info_id']}: {err['error']}")


if __name__ == "__main__":
    main()
