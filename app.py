import streamlit as st
import pandas as pd
import os
from datetime import datetime

# ========== ページ設定 ==========
st.set_page_config(
    page_title="原価さん Pro",
    page_icon="🍱",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ========== スタイル設定 ==========
st.markdown("""
    <style>
    body {
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 10px;
        color: white;
    }
    .success-rate-low {
        background-color: #ffecec;
        color: #d32f2f;
    }
    .success-rate-medium {
        background-color: #fff3cd;
        color: #f57c00;
    }
    .success-rate-high {
        background-color: #e8f5e9;
        color: #388e3c;
    }
    </style>
""", unsafe_allow_html=True)

# ========== データ管理クラス ==========
class DataManager:
    INGREDIENTS_FILE = "data/ingredients.csv"
    RECIPES_FILE = "data/recipes.csv"
    
    def __init__(self):
        os.makedirs("data", exist_ok=True)
        self.ingredients = self._load_ingredients()
        self.recipes = self._load_recipes()
    
    def _load_ingredients(self):
        if os.path.exists(self.INGREDIENTS_FILE):
            df = pd.read_csv(self.INGREDIENTS_FILE)
            df = df.fillna(100)  # デフォルト歩留まり率
            return df
        return pd.DataFrame(columns=['id', 'name', 'unit', 'unit_price', 'yield_rate', 'created_at'])
    
    def _load_recipes(self):
        if os.path.exists(self.RECIPES_FILE):
            return pd.read_csv(self.RECIPES_FILE)
        return pd.DataFrame(columns=['id', 'name', 'selling_price', 'ingredients_json', 'created_at'])
    
    def save_ingredients(self):
        self.ingredients.to_csv(self.INGREDIENTS_FILE, index=False, encoding='utf-8')
    
    def save_recipes(self):
        self.recipes.to_csv(self.RECIPES_FILE, index=False, encoding='utf-8')
    
    def add_ingredient(self, name, unit, unit_price, yield_rate=100):
        new_id = int(self.ingredients['id'].max()) + 1 if len(self.ingredients) > 0 else 1
        new_ingredient = pd.DataFrame({
            'id': [new_id],
            'name': [name],
            'unit': [unit],
            'unit_price': [float(unit_price)],
            'yield_rate': [float(yield_rate)],
            'created_at': [datetime.now().strftime("%Y-%m-%d %H:%M:%S")]
        })
        self.ingredients = pd.concat([self.ingredients, new_ingredient], ignore_index=True)
        self.save_ingredients()
        return True
    
    def delete_ingredient(self, ingredient_id):
        self.ingredients = self.ingredients[self.ingredients['id'] != ingredient_id]
        self.save_ingredients()
    
    def add_recipe(self, name, selling_price):
        new_id = int(self.recipes['id'].max()) + 1 if len(self.recipes) > 0 else 1
        new_recipe = pd.DataFrame({
            'id': [new_id],
            'name': [name],
            'selling_price': [float(selling_price)],
            'ingredients_json': ['[]'],
            'created_at': [datetime.now().strftime("%Y-%m-%d %H:%M:%S")]
        })
        self.recipes = pd.concat([self.recipes, new_recipe], ignore_index=True)
        self.save_recipes()
        return new_id
    
    def delete_recipe(self, recipe_id):
        self.recipes = self.recipes[self.recipes['id'] != recipe_id]
        self.save_recipes()
    
    def get_recipe_by_id(self, recipe_id):
        return self.recipes[self.recipes['id'] == recipe_id].iloc[0] if len(self.recipes[self.recipes['id'] == recipe_id]) > 0 else None
    
    def update_recipe_ingredients(self, recipe_id, ingredients_data):
        """レシピの食材データを更新"""
        import json
        self.recipes.loc[self.recipes['id'] == recipe_id, 'ingredients_json'] = json.dumps(ingredients_data)
        self.save_recipes()

# ========== ユーティリティ関数 ==========
def calculate_ingredient_cost(ingredient_id, quantity, dm):
    """食材の実原価を計算"""
    ingredient = dm.ingredients[dm.ingredients['id'] == ingredient_id]
    if len(ingredient) == 0:
        return 0
    
    unit_price = ingredient['unit_price'].values[0]
    yield_rate = ingredient['yield_rate'].values[0] / 100
    
    # 実原価 = 仕入れ単価 × 使用量 ÷ 歩留まり率
    actual_cost = unit_price * quantity / yield_rate
    return actual_cost

def calculate_recipe_cost(recipe_ingredients, dm):
    """レシピ全体の原価を計算"""
    total_cost = 0
    for ing_id, qty in recipe_ingredients.items():
        total_cost += calculate_ingredient_cost(int(ing_id), qty, dm)
    return total_cost

def get_cost_rate_color(cost_rate):
    """原価率に応じて色を返す"""
    if cost_rate < 30:
        return "green"
    elif cost_rate < 40:
        return "orange"
    else:
        return "red"

# ========== Streamlit セッション状態 ==========
if 'dm' not in st.session_state:
    st.session_state.dm = DataManager()

dm = st.session_state.dm

# ========== メインUI ==========
st.title("🍱 原価さん Pro")
st.subheader("小規模飲食店向け原価管理ツール")

# サイドバー
with st.sidebar:
    st.header("メニュー")
    page = st.radio(
        "移動先を選択",
        ["ホーム", "食材管理", "レシピ管理", "統計情報"]
    )

# ========== ページ1: ホーム ==========
if page == "ホーム":
    st.write("### Excelでの手作業を終わりにしよう")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            label="📊 登録済み食材数",
            value=len(dm.ingredients),
            delta="個"
        )
    
    with col2:
        st.metric(
            label="📋 登録済みメニュー数",
            value=len(dm.recipes),
            delta="個"
        )
    
    with col3:
        if len(dm.recipes) > 0:
            avg_cost_rate = dm.recipes.apply(
                lambda row: (calculate_recipe_cost(
                    {ing_id: qty for ing_id, qty in zip([], [])},
                    dm
                ) / row['selling_price'] * 100) if row['selling_price'] > 0 else 0,
                axis=1
            ).mean()
            st.metric(
                label="📈 平均原価率",
                value=f"{avg_cost_rate:.1f}%",
                delta="average"
            )
    
    st.divider()
    st.write("### 使い方")
    st.write("""
    1. **食材管理** で使う食材を登録
       - 食材名、仕入れ単価、単位、歩留まり率
    
    2. **レシピ管理** でメニューを作成
       - メニュー名、販売価格を入力
    
    3. メニューに食材を追加
       - 使用量を入力すれば原価が自動計算
    
    4. 原価率をチェック
       - 利益率を見直して、メニュー価格を最適化
    """)
    
    st.divider()
    st.write("### 業態別の標準原価率")
    benchmark_data = {
        "業態": ["カフェ", "居酒屋", "ラーメン店", "バー", "イタリアン", "寿司屋"],
        "目安原価率": ["25-35%", "25-35%", "30%", "20-30%", "30-40%", "40-45%"]
    }
    st.dataframe(pd.DataFrame(benchmark_data), use_container_width=True)

# ========== ページ2: 食材管理 ==========
elif page == "食材管理":
    st.write("### 🥬 食材管理")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("#### 食材を追加")
        with st.form("ingredient_form"):
            ingredient_name = st.text_input(
                "食材名",
                placeholder="例：玉ねぎ（L）"
            )
            unit = st.selectbox(
                "単位",
                ["kg", "個", "本", "束", "リットル", "ml", "ケース", "パック"]
            )
            unit_price = st.number_input(
                "単価（円）",
                min_value=0.0,
                step=1.0,
                placeholder="例：100"
            )
            yield_rate = st.slider(
                "歩留まり率（%）",
                min_value=1,
                max_value=100,
                value=100,
                help="100% = 全て可食部。例：玉ねぎは90%（10%は皮や芯）"
            )
            
            if st.form_submit_button("食材を追加", use_container_width=True):
                if ingredient_name and unit_price > 0:
                    dm.add_ingredient(ingredient_name, unit, unit_price, yield_rate)
                    st.success(f"✅ '{ingredient_name}' を追加しました")
                    st.rerun()
                else:
                    st.error("食材名と単価を入力してください")
    
    with col2:
        st.write("#### 登録済み食材")
        if len(dm.ingredients) > 0:
            display_ingredients = dm.ingredients[['name', 'unit_price', 'unit', 'yield_rate']].copy()
            display_ingredients.columns = ['食材名', '単価（円）', '単位', '歩留まり率（%）']
            
            for idx, row in dm.ingredients.iterrows():
                col_a, col_b = st.columns([3, 1])
                with col_a:
                    st.write(f"**{row['name']}**")
                    st.caption(f"¥{row['unit_price']:.0f}/{row['unit']} (歩留まり: {row['yield_rate']}%)")
                with col_b:
                    if st.button("削除", key=f"delete_ing_{row['id']}", use_container_width=True):
                        dm.delete_ingredient(row['id'])
                        st.success("削除しました")
                        st.rerun()
        else:
            st.info("食材がまだ登録されていません")

# ========== ページ3: レシピ管理 ==========
elif page == "レシピ管理":
    st.write("### 📋 レシピ管理")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.write("#### メニューを作成")
        with st.form("recipe_form"):
            recipe_name = st.text_input(
                "メニュー名",
                placeholder="例：焼き玉ねぎ定食"
            )
            selling_price = st.number_input(
                "販売価格（円）",
                min_value=0.0,
                step=100.0
            )
            
            if st.form_submit_button("メニューを作成", use_container_width=True):
                if recipe_name and selling_price > 0:
                    recipe_id = dm.add_recipe(recipe_name, selling_price)
                    st.success(f"✅ メニューを作成しました")
                    st.session_state.selected_recipe_id = recipe_id
                    st.rerun()
                else:
                    st.error("メニュー名と販売価格を入力してください")
    
    with col2:
        st.write("#### メニュー一覧")
        
        if len(dm.recipes) > 0:
            # メニュー選択
            selected_recipe_name = st.selectbox(
                "メニューを選択",
                dm.recipes['name'].values,
                key="recipe_selector"
            )
            
            selected_recipe = dm.recipes[dm.recipes['name'] == selected_recipe_name].iloc[0]
            recipe_id = selected_recipe['id']
            
            st.divider()
            st.write(f"### {selected_recipe['name']}")
            
            col_price, col_cost, col_rate = st.columns(3)
            
            # 食材を JSON から復元
            import json
            try:
                recipe_ingredients = json.loads(selected_recipe['ingredients_json'])
            except:
                recipe_ingredients = {}
            
            # 原価計算
            total_cost = calculate_recipe_cost(recipe_ingredients, dm)
            selling_price = selected_recipe['selling_price']
            cost_rate = (total_cost / selling_price * 100) if selling_price > 0 else 0
            
            with col_price:
                st.metric("販売価格", f"¥{selling_price:.0f}")
            
            with col_cost:
                st.metric("原価", f"¥{total_cost:.0f}")
            
            with col_rate:
                color = get_cost_rate_color(cost_rate)
                st.metric("原価率", f"{cost_rate:.1f}%")
            
            st.divider()
            
            # 食材追加
            if len(dm.ingredients) > 0:
                st.write("#### 食材を追加")
                col_ing, col_qty, col_btn = st.columns([2, 1, 1])
                
                with col_ing:
                    selected_ingredient_name = st.selectbox(
                        "食材を選択",
                        dm.ingredients['name'].values,
                        key=f"ingredient_selector_{recipe_id}"
                    )
                    selected_ingredient = dm.ingredients[dm.ingredients['name'] == selected_ingredient_name].iloc[0]
                
                with col_qty:
                    quantity = st.number_input(
                        "使用量",
                        min_value=0.0,
                        step=0.1,
                        key=f"quantity_{recipe_id}"
                    )
                
                with col_btn:
                    if st.button("追加", key=f"add_ing_btn_{recipe_id}", use_container_width=True):
                        ingredient_id = str(selected_ingredient['id'])
                        recipe_ingredients[ingredient_id] = quantity
                        dm.update_recipe_ingredients(recipe_id, recipe_ingredients)
                        st.success("食材を追加しました")
                        st.rerun()
            
            st.divider()
            
            # 使用食材一覧
            if recipe_ingredients:
                st.write("#### 使用食材")
                for ing_id_str, qty in recipe_ingredients.items():
                    ing_id = int(ing_id_str)
                    ingredient = dm.ingredients[dm.ingredients['id'] == ing_id]
                    
                    if len(ingredient) > 0:
                        ing = ingredient.iloc[0]
                        ing_cost = calculate_ingredient_cost(ing_id, qty, dm)
                        
                        col_name, col_cost, col_del = st.columns([2, 1, 0.5])
                        
                        with col_name:
                            st.write(f"**{ing['name']}**")
                            st.caption(f"{qty}{ing['unit']} (歩留まり: {ing['yield_rate']}%)")
                        
                        with col_cost:
                            st.write(f"¥{ing_cost:.0f}")
                        
                        with col_del:
                            if st.button("🗑️", key=f"delete_ing_from_recipe_{ing_id}"):
                                del recipe_ingredients[ing_id_str]
                                dm.update_recipe_ingredients(recipe_id, recipe_ingredients)
                                st.success("削除しました")
                                st.rerun()
            else:
                st.info("食材がまだ追加されていません")
            
            st.divider()
            
            # メニュー削除
            if st.button("このメニューを削除", use_container_width=True, key=f"delete_recipe_{recipe_id}"):
                dm.delete_recipe(recipe_id)
                st.success("メニューを削除しました")
                st.rerun()
        
        else:
            st.info("メニューがまだ作成されていません")

# ========== ページ4: 統計情報 ==========
elif page == "統計情報":
    st.write("### 📈 統計情報")
    
    if len(dm.recipes) > 0:
        st.write("#### 全メニューの原価率分析")
        
        import json
        recipes_data = []
        
        for _, recipe in dm.recipes.iterrows():
            try:
                recipe_ingredients = json.loads(recipe['ingredients_json'])
            except:
                recipe_ingredients = {}
            
            total_cost = calculate_recipe_cost(recipe_ingredients, dm)
            cost_rate = (total_cost / recipe['selling_price'] * 100) if recipe['selling_price'] > 0 else 0
            
            recipes_data.append({
                'メニュー': recipe['name'],
                '販売価格': recipe['selling_price'],
                '原価': total_cost,
                '原価率': cost_rate,
                '利益': recipe['selling_price'] - total_cost
            })
        
        df_recipes = pd.DataFrame(recipes_data)
        
        # テーブル表示
        st.dataframe(df_recipes, use_container_width=True)
        
        # グラフ
        st.line_chart(df_recipes.set_index('メニュー')['原価率'])
        
        st.divider()
        st.write("#### 推奨事項")
        
        high_cost_recipes = df_recipes[df_recipes['原価率'] > 40]
        if len(high_cost_recipes) > 0:
            st.warning(f"⚠️ 原価率が高いメニュー:")
            for _, row in high_cost_recipes.iterrows():
                st.write(f"- **{row['メニュー']}** (原価率: {row['原価率']:.1f}%) → 価格見直しを検討")
        
        low_profit_recipes = df_recipes[df_recipes['利益'] < 500]
        if len(low_profit_recipes) > 0:
            st.info(f"💡 利益が少ないメニュー:")
            for _, row in low_profit_recipes.iterrows():
                st.write(f"- **{row['メニュー']}** (利益: ¥{row['利益']:.0f})")
    
    else:
        st.info("統計データがまだありません")

# ========== フッター ==========
st.divider()
st.caption("🍱 原価さん Pro | 小規模飲食店向け原価管理ツール")
