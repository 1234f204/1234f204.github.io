import json
import logging
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, jsonify, request, send_from_directory
from price_comparator.scrapers import ALL_SCRAPERS
from price_comparator.processor import DataProcessor
from price_comparator.analyzer import DataAnalyzer
from price_comparator.scrapers.driver import quit_driver

logging.basicConfig(level=logging.INFO)

app = Flask(__name__, static_folder="static", template_folder="templates")


@app.route("/")
def index():
    return send_from_directory(app.template_folder, "index.html")


@app.route("/api/search", methods=["POST"])
def search():
    data = request.get_json() or {}
    keyword = data.get("keyword", "").strip()
    count = data.get("count", 8)
    platforms = data.get("platforms", None)

    if not keyword:
        return jsonify({"error": "关键词不能为空"}), 400

    all_products = []
    errors = []
    selected = ALL_SCRAPERS
    if platforms:
        plat_set = set(platforms)
        selected = [s for s in ALL_SCRAPERS if s.platform_name in plat_set]

    for scraper_cls in selected:
        scraper = scraper_cls()
        try:
            products = scraper.search(keyword, count=count)
            all_products.extend(products)
            if not products:
                errors.append(f"{scraper.platform_name}：未能获取到商品数据，平台可能需要登录或暂时无法访问")
        except Exception as e:
            errors.append(f"{scraper.platform_name}：采集失败 - {str(e)}")

    processor = DataProcessor()
    products = processor.process(all_products, sort_by="price")

    analyzer = DataAnalyzer()
    comparison = analyzer.compare(products)
    trends = analyzer.generate_trends(products)
    summary = analyzer.get_platform_summary(products)

    return jsonify({
        "keyword": keyword,
        "total": len(products),
        "products": [p.to_dict() for p in products],
        "comparison": comparison.to_dict(),
        "trends": [t.to_dict() for t in trends],
        "platform_summary": summary,
        "errors": errors,
    })


@app.route("/api/demo")
def demo():
    demo_data = _get_demo_data()
    return jsonify(demo_data)


def _get_demo_data():
    keyword = "iPhone 16"
    all_products = []
    errors = []
    for scraper_cls in ALL_SCRAPERS:
        scraper = scraper_cls()
        try:
            products = scraper.search(keyword, count=6)
            all_products.extend(products)
            if not products:
                errors.append(f"{scraper.platform_name}：未能获取到商品数据，平台可能需要登录或暂时无法访问")
        except Exception as e:
            errors.append(f"{scraper.platform_name}：采集失败 - {str(e)}")

    processor = DataProcessor()
    products = processor.process(all_products, sort_by="price")

    analyzer = DataAnalyzer()
    comparison = analyzer.compare(products)
    trends = analyzer.generate_trends(products)
    summary = analyzer.get_platform_summary(products)

    return {
        "keyword": keyword,
        "total": len(products),
        "products": [p.to_dict() for p in products],
        "comparison": comparison.to_dict(),
        "trends": [t.to_dict() for t in trends],
        "platform_summary": summary,
        "errors": errors,
    }


@app.teardown_appcontext
def cleanup(exception=None):
    pass


if __name__ == "__main__":
    try:
        app.run(host="0.0.0.0", port=5000, debug=True)
    finally:
        quit_driver()
