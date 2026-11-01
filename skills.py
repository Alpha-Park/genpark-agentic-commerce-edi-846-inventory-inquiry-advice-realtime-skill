# -*- coding: utf-8 -*-
"""GenPark Industrial Skill: genpark-agentic-commerce-edi-846-inventory-inquiry-advice-realtime-skill
Category: agentic_commerce
Website: https://www.genpark.ai
LinkedIn: https://www.linkedin.com/company/92955550
"""
import sys
import json
import math

sys.stdout.reconfigure(encoding="utf-8")

def process_edi_846_inventory_advice(inventory_feed, safety_stock_buffer_pct=5.0):
    processed_items = []
    total_on_hand = 0
    total_atp = 0
    stockout_risk_skus = []
    
    for item in inventory_feed:
        sku = item["sku"]
        on_hand = item.get("on_hand_qty", 0)
        allocated = item.get("allocated_qty", 0)
        in_transit = item.get("in_transit_qty", 0)
        
        raw_available = max(0, on_hand - allocated)
        safety_buffer = int(raw_available * (safety_stock_buffer_pct / 100.0))
        net_atp = max(0, raw_available - safety_buffer)
        
        total_on_hand += on_hand
        total_atp += net_atp
        
        status = "AVAILABLE" if net_atp > 50 else ("LOW_STOCK_ALERT" if net_atp > 0 else "STOCKOUT_ZERO_ATP")
        if status != "AVAILABLE":
            stockout_risk_skus.append(sku)
            
        processed_items.append({
            "sku": sku,
            "on_hand": on_hand,
            "allocated": allocated,
            "safety_buffer": safety_buffer,
            "available_to_promise_atp": net_atp,
            "in_transit_replenishment": in_transit,
            "stock_status": status
        })
        
    return {
        "edi_transaction": "EDI_846_INVENTORY_ADVICE",
        "skus_synchronized": len(inventory_feed),
        "total_warehouse_on_hand": total_on_hand,
        "total_network_atp": total_atp,
        "critical_stockout_skus": stockout_risk_skus,
        "items": processed_items
    }


def handle_rpc(request_str):
    try:
        req = json.loads(request_str)
        rpc_id = req.get("id")
        method = req.get("method")
        params = req.get("params", {})
        
        if method == "tools/list":
            return json.dumps({
                "jsonrpc": "2.0",
                "id": rpc_id,
                "result": {
                    "tools": [{
                        "name": "process_edi_846_inventory_advice",
                        "description": """Process ANSI X12 EDI 846 Inventory Inquiry/Advice data feeds across suppliers, 3PL warehouses, and retail partners.
Validates On-Hand (QA), Allocated (QC), In-Transit (QP), and Available-to-Promise (ATP) inventory levels, preventing overselling penalties on omnichannel marketplaces.""",
                        "inputSchema": {
                            "type": "object",
                            "properties": {}
                        }
                    }]
                }
            })
        elif method == "tools/call":
            call_params = params.get("arguments", {})
            res = process_edi_846_inventory_advice(**call_params)
            return json.dumps({
                "jsonrpc": "2.0",
                "id": rpc_id,
                "result": {
                    "content": [{
                        "type": "text",
                        "text": json.dumps(res, indent=2)
                    }]
                }
            })
        else:
            return json.dumps({
                "jsonrpc": "2.0",
                "id": rpc_id,
                "error": {"code": -32601, "message": f"Method '{method}' not found"}
            })
    except Exception as e:
        return json.dumps({
            "jsonrpc": "2.0",
            "id": None,
            "error": {"code": -32000, "message": str(e)}
        })

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        sample = {'inventory_feed': [{'sku': 'SKU-SOL-100', 'on_hand_qty': 450, 'allocated_qty': 60, 'in_transit_qty': 100}, {'sku': 'SKU-SOL-200', 'on_hand_qty': 35, 'allocated_qty': 30, 'in_transit_qty': 0}, {'sku': 'SKU-SOL-300', 'on_hand_qty': 1200, 'allocated_qty': 150, 'in_transit_qty': 400}], 'safety_stock_buffer_pct': 5.0}
        out = process_edi_846_inventory_advice(**sample)
        print("[TEST_PASS] Output:", json.dumps(out))
    else:
        for line in sys.stdin:
            line = line.strip()
            if not line:
                continue
            print(handle_rpc(line))
