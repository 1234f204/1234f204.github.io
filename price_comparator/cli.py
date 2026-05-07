import json
import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from .scrapers import ALL_SCRAPERS
from .processor import DataProcessor
from .analyzer import DataAnalyzer

console = Console()


def fetch_products(keyword: str, count: int = 8, platforms: str = None):
    all_products = []
    selected = ALL_SCRAPERS
    if platforms:
        plat_set = set(p.strip() for p in platforms.split(","))
        selected = [s for s in ALL_SCRAPERS if s.platform_name in plat_set]
    for scraper_cls in selected:
        scraper = scraper_cls()
        console.print(f"[cyan]🔍 正在从 {scraper.platform_name} 采集 '{keyword}' ...[/cyan]")
        products = scraper.search(keyword, count=count)
        all_products.extend(products)
        console.print(f"[green]  ✓ {scraper.platform_name}: 获取 {len(products)} 条结果[/green]")
    return all_products


@click.group()
@click.version_option("1.0.0")
def cli():
    """电商商品价格采集与对比工具"""
    pass


@cli.command()
@click.argument("keyword")
@click.option("-n", "--count", default=8, help="每个平台采集数量")
@click.option("-p", "--platforms", default=None, help="指定平台(逗号分隔): 京东,淘宝,拼多多")
@click.option("-s", "--sort", "sort_by", default="price", help="排序方式: price/sales/rating/discount")
@click.option("--min-price", default=None, type=float, help="最低价格过滤")
@click.option("--max-price", default=None, type=float, help="最高价格过滤")
@click.option("-o", "--output", default=None, help="导出JSON文件路径")
def search(keyword, count, platforms, sort_by, min_price, max_price, output):
    """按关键词搜索商品并展示结果"""
    all_products = fetch_products(keyword, count, platforms)
    processor = DataProcessor()
    products = processor.process(all_products, sort_by=sort_by)
    if min_price is not None:
        products = processor.filter_by_price_range(products, min_price=min_price,
                                                    max_price=max_price or float("inf"))
    elif max_price is not None:
        products = processor.filter_by_price_range(products, max_price=max_price)

    console.print(f"\n[bold yellow]═══ 搜索结果: '{keyword}' (共 {len(products)} 条) ═══[/bold yellow]\n")
    _render_product_table(products)

    if output:
        data = [p.to_dict() for p in products]
        with open(output, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        console.print(f"\n[green]✓ 数据已导出到 {output}[/green]")


@cli.command()
@click.argument("keyword")
@click.option("-n", "--count", default=8, help="每个平台采集数量")
@click.option("-p", "--platforms", default=None, help="指定平台(逗号分隔)")
@click.option("-o", "--output", default=None, help="导出JSON文件路径")
def compare(keyword, count, platforms, output):
    """跨平台对比商品价格与性价比"""
    all_products = fetch_products(keyword, count, platforms)
    processor = DataProcessor()
    products = processor.process(all_products, sort_by="price")
    analyzer = DataAnalyzer()
    result = analyzer.compare(products)
    summary = analyzer.get_platform_summary(products)

    console.print(f"\n[bold yellow]═══ 跨平台对比: '{keyword}' ═══[/bold yellow]\n")
    _render_product_table(products, show_value=True, value_scores=result.value_scores)

    console.print(f"\n[bold cyan]📊 平台汇总[/bold cyan]")
    _render_summary_table(summary)

    console.print(f"\n[bold green]🏆 推荐结果[/bold green]")
    if result.best_price:
        console.print(f"  💰 最低价: [bold]{result.best_price.name}[/bold] - "
                      f"[red]¥{result.best_price.price}[/red] ({result.best_price.platform})")
    if result.best_value:
        console.print(f"  ⭐ 最佳性价比: [bold]{result.best_value.name}[/bold] - "
                      f"[red]¥{result.best_value.price}[/red] ({result.best_value.platform})")
    console.print(f"  📈 价格区间: ¥{result.price_range[0]:.2f} ~ ¥{result.price_range[1]:.2f}")
    console.print(f"  📊 平均价: ¥{result.avg_price:.2f}")

    if output:
        data = result.to_dict()
        data["platform_summary"] = summary
        with open(output, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        console.print(f"\n[green]✓ 对比数据已导出到 {output}[/green]")


@cli.command()
@click.argument("keyword")
@click.option("-n", "--count", default=8, help="每个平台采集数量")
@click.option("-d", "--days", default=7, help="趋势天数")
@click.option("-p", "--platforms", default=None, help="指定平台(逗号分隔)")
@click.option("-o", "--output", default=None, help="导出JSON文件路径")
def trend(keyword, count, days, platforms, output):
    """查看商品价格趋势"""
    all_products = fetch_products(keyword, count, platforms)
    processor = DataProcessor()
    products = processor.process(all_products)
    analyzer = DataAnalyzer()
    trends = analyzer.generate_trends(products, days=days)

    console.print(f"\n[bold yellow]═══ 价格趋势: '{keyword}' (近{days}天) ═══[/bold yellow]\n")

    for t in trends:
        console.print(f"[cyan]{t.product_name}[/cyan]")
        trend_line = "  "
        max_p = max(t.prices)
        min_p = min(t.prices)
        for i, (d, p) in enumerate(zip(t.dates, t.prices)):
            bar_len = int((p - min_p) / (max_p - min_p + 0.01) * 20)
            bar = "█" * (bar_len + 1)
            trend_line += f"{d}: [green]¥{p:>8.2f}[/green] {bar}\n  "
        console.print(trend_line)

    if output:
        data = [t.to_dict() for t in trends]
        with open(output, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        console.print(f"\n[green]✓ 趋势数据已导出到 {output}[/green]")


def _render_product_table(products, show_value=False, value_scores=None):
    table = Table(show_header=True, header_style="bold magenta", row_styles=["dim", ""])
    table.add_column("#", style="dim", width=4)
    table.add_column("商品名称", max_width=35)
    table.add_column("平台", width=8)
    table.add_column("价格", justify="right", width=10)
    table.add_column("原价", justify="right", width=10)
    table.add_column("折扣", justify="right", width=8)
    table.add_column("销量", justify="right", width=12)
    table.add_column("店铺评分", justify="right", width=8)
    table.add_column("店铺", max_width=18)

    if show_value:
        table.add_column("性价比", justify="right", width=8)

    score_map = {}
    if value_scores:
        for s in value_scores:
            score_map[s["product_id"]] = s["score"]

    for i, p in enumerate(products, 1):
        discount_str = f"-{p.discount_rate * 100:.1f}%" if p.discount_rate > 0 else "-"
        sales_str = _format_sales(p.sales)
        row = [
            str(i),
            p.name[:35],
            p.platform,
            f"¥{p.price:.2f}",
            f"¥{p.original_price:.2f}" if p.original_price else "-",
            discount_str,
            sales_str,
            f"{p.store_rating:.1f}",
            p.store_name[:18],
        ]
        if show_value:
            score = score_map.get(p.id, 0)
            score_str = f"{score:.3f}"
            row.append(score_str)
        table.add_row(*row)

    console.print(table)


def _render_summary_table(summary):
    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("平台", width=10)
    table.add_column("商品数", justify="right", width=8)
    table.add_column("均价", justify="right", width=10)
    table.add_column("最低价", justify="right", width=10)
    table.add_column("最高价", justify="right", width=10)
    table.add_column("平均评分", justify="right", width=10)
    table.add_column("总销量", justify="right", width=14)

    for s in summary:
        table.add_row(
            s["platform"],
            str(s["count"]),
            f"¥{s['avg_price']:.2f}",
            f"¥{s['min_price']:.2f}",
            f"¥{s['max_price']:.2f}",
            f"{s['avg_rating']:.1f}",
            _format_sales(s["total_sales"]),
        )
    console.print(table)


def _format_sales(sales: int) -> str:
    if sales >= 10000:
        return f"{sales / 10000:.1f}万+"
    return f"{sales:,}"


def main():
    cli()


if __name__ == "__main__":
    main()
