import sys
import datetime
import re
from lunardate import LunarDate

# # --- 离线笔画库 ---
# from strokes import strokes

# # 1. 查单个字的笔画
# count = strokes('梅')
# print(f"梅的笔画数: {count}") 
# # 输出: 11

# # 2. 查一个词或一句话的笔画
# word_counts = strokes('梅花易数')
# print(f"梅花易数的笔画: {word_counts}") 
# # 输出: [11, 7, 8, 13]
# # -----------------

# --- 基础数据与字典 ---
BAGUA = {
    1: {'name': '乾', 'element': '金', 'yaos': [1, 1, 1]},
    2: {'name': '兑', 'element': '金', 'yaos': [1, 1, 0]},
    3: {'name': '离', 'element': '火', 'yaos': [1, 0, 1]},
    4: {'name': '震', 'element': '木', 'yaos': [1, 0, 0]},
    5: {'name': '巽', 'element': '木', 'yaos': [0, 1, 1]},
    6: {'name': '坎', 'element': '水', 'yaos': [0, 1, 0]},
    7: {'name': '艮', 'element': '土', 'yaos': [0, 0, 1]},
    8: {'name': '坤', 'element': '土', 'yaos': [0, 0, 0]}
}

HEXAGRAMS = {
    (1,1):'乾为天', (1,2):'天泽履', (1,3):'天火同人', (1,4):'天雷无妄', (1,5):'天风姤', (1,6):'天水讼', (1,7):'天山遁', (1,8):'天地否',
    (2,1):'泽天夬', (2,2):'兑为泽', (2,3):'泽火革', (2,4):'泽雷随', (2,5):'泽风大过', (2,6):'泽水困', (2,7):'泽山咸', (2,8):'泽地萃',
    (3,1):'火天大有', (3,2):'火泽睽', (3,3):'离为火', (3,4):'火雷噬嗑', (3,5):'火风鼎', (3,6):'火水未济', (3,7):'火山旅', (3,8):'火地晋',
    (4,1):'雷天大壮', (4,2):'雷泽归妹', (4,3):'雷火丰', (4,4):'震为雷', (4,5):'雷风恒', (4,6):'雷水解', (4,7):'雷山小过', (4,8):'雷地豫',
    (5,1):'风天小畜', (5,2):'风泽中孚', (5,3):'风火家人', (5,4):'风雷益', (5,5):'巽为风', (5,6):'风水涣', (5,7):'风山渐', (5,8):'风地观',
    (6,1):'水天需', (6,2):'水泽节', (6,3):'水火既济', (6,4):'水雷屯', (6,5):'水风井', (6,6):'坎为水', (6,7):'水山蹇', (6,8):'水地比',
    (7,1):'山天大畜', (7,2):'山泽损', (7,3):'山火贲', (7,4):'山雷颐', (7,5):'山风蛊', (7,6):'山水蒙', (7,7):'艮为山', (7,8):'山地剥',
    (8,1):'地天泰', (8,2):'地泽临', (8,3):'地火明夷', (8,4):'地雷复', (8,5):'地风升', (8,6):'地水师', (8,7):'地山谦', (8,8):'坤为地'
}

BRANCHES = ["", "子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]

# --- 核心逻辑函数 ---
def get_mod(val, base):
    res = val % base
    return res if res != 0 else base

def yaos_to_gua(yaos):
    for idx, data in BAGUA.items():
        if data['yaos'] == yaos: return idx
    return None

def calculate_hexagrams(upper_idx, lower_idx, moving_yao):
    ben_yaos = BAGUA[lower_idx]['yaos'] + BAGUA[upper_idx]['yaos']
    hu_lower_idx = yaos_to_gua(ben_yaos[1:4])
    hu_upper_idx = yaos_to_gua(ben_yaos[2:5])
    
    bian_yaos = ben_yaos.copy()
    bian_yaos[moving_yao - 1] = 1 - bian_yaos[moving_yao - 1]
    bian_lower_idx = yaos_to_gua(bian_yaos[0:3])
    bian_upper_idx = yaos_to_gua(bian_yaos[3:6])
    
    return {
        'ben': (upper_idx, lower_idx),
        'hu': (hu_upper_idx, hu_lower_idx),
        'bian': (bian_upper_idx, bian_lower_idx)
    }

def get_gua_qi(element, month):
    if month in [1, 2, 3]: season_ele = '木'
    elif month in [4, 5, 6]: season_ele = '火'
    elif month in [7, 8, 9]: season_ele = '金'
    else: season_ele = '水'
    
    relations = {
        '木': {'木': '旺', '火': '相', '水': '休', '金': '囚', '土': '死'},
        '火': {'火': '旺', '土': '相', '木': '休', '水': '囚', '金': '死'},
        '金': {'金': '旺', '水': '相', '土': '休', '火': '囚', '木': '死'},
        '水': {'水': '旺', '木': '相', '金': '休', '土': '囚', '火': '死'},
        '土': {'土': '旺', '金': '相', '火': '休', '木': '囚', '水': '死'}
    }
    return relations[season_ele].get(element, '未知')

def get_current_time_info():
    """获取当前系统时间并转化为农历与地支数"""
    now = datetime.datetime.now()
    lunar_now = LunarDate.fromSolarDate(now.year, now.month, now.day)
    
    year_idx = (lunar_now.year - 3) % 12
    year_idx = 12 if year_idx == 0 else year_idx
    
    hour_idx = ((now.hour + 1) % 24) // 2 + 1
    
    return {
        'year_idx': year_idx,
        'month': lunar_now.month,
        'day': lunar_now.day,
        'hour_idx': hour_idx,
        'lunar_str': f"农历 {BRANCHES[year_idx]}年 {lunar_now.month}月 {lunar_now.day}日 {BRANCHES[hour_idx]}时",
        'solar_str': now.strftime("%Y-%m-%d %H:%M:%S")
    }

# --- 主交互流程 ---
def main():
    print("=" * 50)
    print("【Jayden的梅花易数排盘计算器】支持以下三种输入格式：")
    print("1. 时间起卦：直接输入 '时间'")
    print("2. 数字起卦：直接输入数字 (例: '3 6 9' 或 '12 37 18')")
    print("3. 笔画起卦：输入'笔画'加数字 (例: '笔画12 3 9' 或 '笔画 15 7')")
    print("=" * 50)
    
    user_input = input("请输入: ").strip()
    
    if not user_input:
        print("未检测到输入，程序退出。")
        return

    # 自动获取当前时间
    time_info = get_current_time_info()
    month = time_info['month']
    hour_idx = time_info['hour_idx']
    
    try:
        if user_input == "时间":
            mode_name = "时间起卦"
            input_display = "当前时间"
            
            upper_sum = time_info['year_idx'] + month + time_info['day']
            lower_sum = upper_sum + hour_idx
            total_sum = lower_sum
            
            upper_idx = get_mod(upper_sum, 8)
            lower_idx = get_mod(lower_sum, 8)
            moving_yao = get_mod(total_sum, 6)

        else:
            if user_input.startswith("笔画"):
                mode_name = "汉字笔画起卦"
                num_str = user_input.replace("笔画", "").strip()
            else:
                mode_name = "数字起卦"
                num_str = user_input
                
            nums = [int(x) for x in re.split(r'[ ,，]+', num_str) if x]
            input_display = " ".join(map(str, nums))
            
            if len(nums) < 2:
                raise ValueError("规则限制：单个数字/笔画无法产生回应，请至少输入2个及以上数字。")
            
            mid = len(nums) // 2
            upper_sum = sum(nums[:mid])
            lower_sum = sum(nums[mid:])
            total_sum = sum(nums) + hour_idx
            
            upper_idx = get_mod(upper_sum, 8)
            lower_idx = get_mod(lower_sum, 8)
            moving_yao = get_mod(total_sum, 6)

        # 核心推演
        res = calculate_hexagrams(upper_idx, lower_idx, moving_yao)
        
        # 判断体用
        ti_idx = lower_idx if moving_yao > 3 else upper_idx
        yong_idx = upper_idx if moving_yao > 3 else lower_idx
        ti_position = "下卦" if moving_yao > 3 else "上卦"
        yong_position = "上卦" if moving_yao > 3 else "下卦"
        
        ti_gua = BAGUA[ti_idx]
        yong_gua = BAGUA[yong_idx]
        ti_qi = get_gua_qi(ti_gua['element'], month)
        yong_qi = get_gua_qi(yong_gua['element'], month)
        
        # 提取互卦、变卦的上下卦信息
        hu_up, hu_down = res['hu']
        bian_up, bian_down = res['bian']
        
        hu_up_gua, hu_down_gua = BAGUA[hu_up], BAGUA[hu_down]
        bian_up_gua, bian_down_gua = BAGUA[bian_up], BAGUA[bian_down]
        
        # === 终端打印排盘结果 ===
        print("\n\n" + "=" * 45)
        print("【梅花易数 · 排盘结果】")
        print("-" * 45)
        print(f"公历时间：{time_info['solar_str']}")
        print(f"农历排盘：{time_info['lunar_str']}")
        print(f"起卦方式：{mode_name} ({input_display})")
        print("-" * 45)
        print(f"本卦：《{HEXAGRAMS[res['ben']]}》 (上{BAGUA[res['ben'][0]]['name']}下{BAGUA[res['ben'][1]]['name']})")
        print(f"互卦：《{HEXAGRAMS[res['hu']]}》 (上{BAGUA[res['hu'][0]]['name']}下{BAGUA[res['hu'][1]]['name']})")
        print(f"变卦：《{HEXAGRAMS[res['bian']]}》 (上{BAGUA[res['bian'][0]]['name']}下{BAGUA[res['bian'][1]]['name']})")
        print(f"动爻：第 {moving_yao} 爻动")
        print("-" * 45)
        print(f"体用：体卦为 {ti_gua['name']}({ti_gua['element']})居{ti_position}，用卦为 {yong_gua['name']}({yong_gua['element']})居{yong_position}")
        print(f"本卦卦气：当前农历 {month} 月，体卦气【{ti_qi}】，用卦气【{yong_qi}】")
        print(f"互卦卦气：上卦{hu_up_gua['name']}({hu_up_gua['element']})气【{get_gua_qi(hu_up_gua['element'], month)}】，下卦{hu_down_gua['name']}({hu_down_gua['element']})气【{get_gua_qi(hu_down_gua['element'], month)}】")
        print(f"变卦卦气：上卦{bian_up_gua['name']}({bian_up_gua['element']})气【{get_gua_qi(bian_up_gua['element'], month)}】，下卦{bian_down_gua['name']}({bian_down_gua['element']})气【{get_gua_qi(bian_down_gua['element'], month)}】")
        print("=" * 45 + "\n")
        
    except Exception as e:
        print(f"\n❌ 排盘失败：{e}。请检查输入格式。")

if __name__ == "__main__":
    main()