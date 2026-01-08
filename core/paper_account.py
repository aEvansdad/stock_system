# core/paper_account.py
import json
import os
from datetime import datetime

class PaperAccount:
    def __init__(self, data_file='data/paper_account.json'):
        self.data_file = data_file
        self.load_account()

    def load_account(self):
        """加载账户数据，如果不存在则初始化"""
        if os.path.exists(self.data_file):
            with open(self.data_file, 'r') as f:
                self.data = json.load(f)
        else:
            self.data = {"cash": 100000.0, "positions": {}, "history": []}
            self.save_account()

    def save_account(self):
        """保存账户数据到硬盘"""
        with open(self.data_file, 'w') as f:
            json.dump(self.data, f, indent=4)

    def get_balance(self):
        return self.data['cash']

    def get_positions(self):
        return self.data['positions']

    def execute_trade(self, symbol, action, price, quantity):
        """
        执行交易
        :param action: "BUY" or "SELL"
        """
        cost = price * quantity
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if action == "BUY":
            if self.data['cash'] >= cost:
                self.data['cash'] -= cost
                # 更新持仓
                current_qty = self.data['positions'].get(symbol, {}).get('qty', 0)
                # 简单计算平均成本 (Average Cost)
                current_avg = self.data['positions'].get(symbol, {}).get('avg_price', 0)
                new_avg = ((current_qty * current_avg) + cost) / (current_qty + quantity)
                
                self.data['positions'][symbol] = {
                    'qty': current_qty + quantity,
                    'avg_price': new_avg
                }
                # 记录流水
                self.log_transaction(timestamp, symbol, "BUY", price, quantity)
                self.save_account()
                return True, "✅ 买入成功"
            else:
                return False, "❌ 资金不足"

        elif action == "SELL":
            current_qty = self.data['positions'].get(symbol, {}).get('qty', 0)
            if current_qty >= quantity:
                self.data['cash'] += cost
                # 更新持仓
                remaining_qty = current_qty - quantity
                if remaining_qty == 0:
                    del self.data['positions'][symbol]
                else:
                    self.data['positions'][symbol]['qty'] = remaining_qty
                
                # 记录流水
                self.log_transaction(timestamp, symbol, "SELL", price, quantity)
                self.save_account()
                return True, "✅ 卖出成功"
            else:
                return False, "❌ 持仓不足"
        
        return False, "未知操作"

    def log_transaction(self, time, symbol, action, price, qty):
        record = {
            "time": time,
            "symbol": symbol,
            "action": action,
            "price": price,
            "qty": qty,
            "amount": price * qty
        }
        self.data['history'].insert(0, record) # 把最新的插到最前面