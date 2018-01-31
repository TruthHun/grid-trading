# coding=utf-8
from __future__ import print_function, absolute_import, unicode_literals
import numpy as np
import pandas as pd
from gm.api import *
'''
本策略首先计算了过去300个价格数据的均值和标准差
并根据均值加减1和2个标准差得到网格的区间分界线,
并分别配以0.3和0.5的仓位权重
然后根据价格所在的区间来配置仓位(+/-40为上下界,无实际意义):
(-40,-3],(-3,-2],(-2,2],(2,3],(3,40](具体价格等于均值+数字倍标准差)
[-0.5, -0.3, 0.0, 0.3, 0.5](资金比例,此处负号表示开空仓)
回测数据为:SHFE.rb1801的1min数据
回测时间为:2017-07-01 08:00:00到2017-10-01 16:00:00
'''
def init(context):
    context.symbol = 'SHFE.rb1801'
    # 订阅SHFE.rb1801, bar频率为1min
    subscribe(symbols=context.symbol, frequency='60s')
    # 获取过去300个价格数据
    timeseries = history_n(symbol=context.symbol, frequency='60s', count=300, fields='close', fill_missing='Last',
                           end_time='2017-07-01 08:00:00', df=True)['close'].values
    # 获取网格区间分界线
    context.band = np.mean(timeseries) + np.array([-40, -3, -2, 2, 3, 40]) * np.std(timeseries)
    # 设置网格的仓位
    context.weight = [0.5, 0.3, 0.0, 0.3, 0.5]
def on_bar(context, bars):
    bar = bars[0]
    # 根据价格落在(-40,-3],(-3,-2],(-2,2],(2,3],(3,40]的区间范围来获取最新收盘价所在的价格区间
    grid = pd.cut([bar.close], context.band, labels=[0, 1, 2, 3, 4])[0]
    # 获取多仓仓位
    position_long = context.account().position(symbol=context.symbol, side=PositionSide_Long)
    # 获取空仓仓位
    position_short = context.account().position(symbol=context.symbol, side=PositionSide_Short)
    # 若无仓位且价格突破则按照设置好的区间开仓
    if not position_long and not position_short and grid != 2:
        # 大于3为在中间网格的上方,做多
        if grid >= 3:
            order_target_percent(symbol=context.symbol, percent=context.weight[grid], order_type=OrderType_Market,
                                 position_side=PositionSide_Long)
            print(context.symbol, '以市价单开多仓到仓位', context.weight[grid])
        if grid <= 1:
            order_target_percent(symbol=context.symbol, percent=context.weight[grid], order_type=OrderType_Market,
                                 position_side=PositionSide_Short)
            print(context.symbol, '以市价单开空仓到仓位', context.weight[grid])
    # 持有多仓的处理
    elif position_long:
        if grid >= 3:
            order_target_percent(symbol=context.symbol, percent=context.weight[grid], order_type=OrderType_Market,
                                 position_side=PositionSide_Long)
            print(context.symbol, '以市价单调多仓到仓位', context.weight[grid])
        # 等于2为在中间网格,平仓
        elif grid == 2:
            order_target_percent(symbol=context.symbol, percent=0, order_type=OrderType_Market,
                                 position_side=PositionSide_Long)
            print(context.symbol, '以市价单全平多仓')
        # 小于1为在中间网格的下方,做空
        elif grid <= 1:
            order_target_percent(symbol=context.symbol, percent=0, order_type=OrderType_Market,
                                 position_side=PositionSide_Long)
            print(context.symbol, '以市价单全平多仓')
            order_target_percent(symbol=context.symbol, percent=context.weight[grid], order_type=OrderType_Market,
                                 position_side=PositionSide_Short)
            print(context.symbol, '以市价单开空仓到仓位', context.weight[grid])
    # 持有空仓的处理
    elif position_short:
        # 小于1为在中间网格的下方,做空
        if grid <= 1:
            order_target_percent(symbol=context.symbol, percent=context.weight[grid], order_type=OrderType_Market,
                                 position_side=PositionSide_Short)
            print(context.symbol, '以市价单调空仓到仓位', context.weight[grid])
        # 等于2为在中间网格,平仓
        elif grid == 2:
            order_target_percent(symbol=context.symbol, percent=0, order_type=OrderType_Market,
                                 position_side=PositionSide_Short)
            print(context.symbol, '以市价单全平空仓')
        # 大于3为在中间网格的上方,做多
        elif grid >= 3:
            order_target_percent(symbol=context.symbol, percent=0, order_type=OrderType_Market,
                                 position_side=PositionSide_Short)
            print(context.symbol, '以市价单全平空仓')
            order_target_percent(symbol=context.symbol, percent=context.weight[grid], order_type=OrderType_Market,
                                 position_side=PositionSide_Long)
            print(context.symbol, '以市价单开多仓到仓位', context.weight[grid])
if __name__ == '__main__':
    '''
    strategy_id策略ID,由系统生成
    filename文件名,请与本文件名保持一致
    mode实时模式:MODE_LIVE回测模式:MODE_BACKTEST
    token绑定计算机的ID,可在系统设置-密钥管理中生成
    backtest_start_time回测开始时间
    backtest_end_time回测结束时间
    backtest_adjust股票复权方式不复权:ADJUST_NONE前复权:ADJUST_PREV后复权:ADJUST_POST
    backtest_initial_cash回测初始资金
    backtest_commission_ratio回测佣金比例
    backtest_slippage_ratio回测滑点比例
    '''
    run(strategy_id='strategy_id',
        filename='main.py',
        mode=MODE_BACKTEST,
        token='token_id',
        backtest_start_time='2017-07-01 08:00:00',
        backtest_end_time='2017-10-01 16:00:00',
        backtest_adjust=ADJUST_PREV,
        backtest_initial_cash=10000000,
        backtest_commission_ratio=0.0001,
        backtest_slippage_ratio=0.0001)