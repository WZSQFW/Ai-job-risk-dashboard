import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
import sys

# ========== 强制切换到 app.py 所在目录 ==========
if getattr(sys, 'frozen', False):
    script_dir = os.path.dirname(sys.executable)
else:
    script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)

# ========== 文件路径（直接使用相对路径）==========
PANEL_FILE = "province_industry_exposure_final.csv"
OCC_FILE = "中国职业_AI替代风险指数.csv"

# 检查文件是否存在
if not os.path.exists(PANEL_FILE):
    st.error(f"❌ 文件未找到: {PANEL_FILE}\n当前目录: {os.getcwd()}\n请确保该文件与 app.py 在同一文件夹。")
    st.stop()
if not os.path.exists(OCC_FILE):
    st.error(f"❌ 文件未找到: {OCC_FILE}\n当前目录: {os.getcwd()}\n请确保该文件与 app.py 在同一文件夹。")
    st.stop()

# ========== 页面配置 ==========
st.set_page_config(page_title="AI职业替代风险预警系统", page_icon="🤖", layout="wide", initial_sidebar_state="expanded")

# 自定义CSS（突出表格和预警等级）
st.markdown("""
<style>
    .main-title {
        background: linear-gradient(120deg, #1e3c72, #2a5298);
        padding: 1rem;
        border-radius: 15px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: #f8f9fa;
        border-radius: 12px;
        padding: 1rem;
        text-align: center;
        border-top: 3px solid #2a5298;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    /* 预警标签样式 */
    .warning-red { color: #d32f2f; font-weight: bold; background: #ffebee; padding: 0.2rem 0.8rem; border-radius: 20px; display: inline-block; }
    .warning-orange { color: #f57c00; font-weight: bold; background: #fff3e0; padding: 0.2rem 0.8rem; border-radius: 20px; display: inline-block; }
    .warning-yellow { color: #f1c40f; font-weight: bold; background: #fffde7; padding: 0.2rem 0.8rem; border-radius: 20px; display: inline-block; }
    .warning-blue { color: #1976d2; font-weight: bold; background: #e3f2fd; padding: 0.2rem 0.8rem; border-radius: 20px; display: inline-block; }
    /* 数据表格突出就业人数列 */
    .dataframe td:nth-child(3) { font-weight: bold; background-color: #f0f7ff; }
    .dataframe th { background-color: #e8f0fe; }
</style>
""", unsafe_allow_html=True)

st.markdown(
    '<div class="main-title"><h1>🤖 AI职业替代风险预警系统</h1><p>服务国家“稳就业”战略 —— 基于多源职业任务数据的统计模型</p></div>',
    unsafe_allow_html=True)


# ========== 加载数据 ==========
@st.cache_data
def load_data():
    panel = pd.read_csv(PANEL_FILE)
    occ_risk = pd.read_csv(OCC_FILE)
    if 'china_name' not in occ_risk.columns and '职业名称' in occ_risk.columns:
        occ_risk.rename(columns={'职业名称': 'china_name'}, inplace=True)
    if 'risk_ensemble' not in occ_risk.columns and 'risk_final' in occ_risk.columns:
        occ_risk.rename(columns={'risk_final': 'risk_ensemble'}, inplace=True)
    return panel, occ_risk


panel_df, occ_df = load_data()

# 计算全国行业平均暴露度及预警阈值
industry_avg_national = panel_df.groupby('industry')['exposure'].mean().reset_index()
q25 = industry_avg_national['exposure'].quantile(0.25)
q50 = industry_avg_national['exposure'].quantile(0.50)
q75 = industry_avg_national['exposure'].quantile(0.75)


def warning_level(x):
    if x > q75:
        return '红色预警'
    elif x > q50:
        return '橙色预警'
    elif x > q25:
        return '黄色预警'
    else:
        return '蓝色安全'


def warning_style(level):
    if level == '红色预警':
        return 'warning-red'
    elif level == '橙色预警':
        return 'warning-orange'
    elif level == '黄色预警':
        return 'warning-yellow'
    else:
        return 'warning-blue'


color_map = {'红色预警': '#d32f2f', '橙色预警': '#f57c00', '黄色预警': '#f1c40f', '蓝色安全': '#1976d2'}
industry_avg_national['预警等级'] = industry_avg_national['exposure'].apply(warning_level)

# ========== 侧边栏导航 ==========
st.sidebar.title("📌 导航菜单")
option = st.sidebar.radio("请选择功能",
                          ["🔍 职业风险查询", "📊 行业风险地图", "🗺️ 地区风险面板", "⚠️ 预警面板", "📝 政策建议"], index=0)

# ========== 功能1：职业风险查询 ==========
if option == "🔍 职业风险查询":
    st.subheader("🔍 职业AI替代风险查询")
    occ_list = sorted(occ_df['china_name'].dropna().unique())
    selected_occ = st.selectbox("选择或输入职业名称", occ_list)
    risk_val = occ_df[occ_df['china_name'] == selected_occ]['risk_ensemble'].values[0]

    if risk_val < 0.2:
        level, color, desc = "极低风险", "green", "该职业的任务高度依赖创造力、复杂决策或人际互动，AI短期内难以替代。"
    elif risk_val < 0.4:
        level, color, desc = "低风险", "blue", "该职业部分任务可自动化，但核心职责仍需人类判断。"
    elif risk_val < 0.6:
        level, color, desc = "中风险", "orange", "该职业有较多常规性任务，建议关注AI进展，提前学习互补技能。"
    elif risk_val < 0.8:
        level, color, desc = "高风险", "red", "该职业大量任务可被AI替代，建议立即规划技能升级或转岗。"
    else:
        level, color, desc = "极高风险", "darkred", "该职业是AI替代的重点目标，强烈建议转向更需人类特质的岗位。"

    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        st.markdown(f'<div class="metric-card"><h3>📊 风险指数</h3><h2 style="color:{color}">{risk_val:.3f}</h2></div>',
                    unsafe_allow_html=True)
    with col2:
        st.markdown(f'<div class="metric-card"><h3>⚡ 风险等级</h3><h2 style="color:{color}">{level}</h2></div>',
                    unsafe_allow_html=True)
    with col3:
        st.info(f"💡 {desc}")

    with st.expander("📖 什么是AI替代风险指数？"):
        st.markdown(
            "- 指数范围0~1，越接近1越易被AI替代。\n- 基于O*NET职业任务数据中的重要性×水平评分，通过PCA+随机森林集成计算。\n- 高风险职业：重复性、程序化；低风险职业：创意、管理、情感交流。")

# ========== 功能2：行业风险地图 ==========
elif option == "📊 行业风险地图":
    st.subheader("📊 各行业AI暴露度对比（全国平均）")
    industry_sorted = industry_avg_national.sort_values('exposure', ascending=True)
    colors = [color_map[lvl] for lvl in industry_sorted['预警等级']]
    fig = go.Figure(go.Bar(x=industry_sorted['exposure'], y=industry_sorted['industry'], orientation='h',
                           marker_color=colors, text=industry_sorted['exposure'].round(3), textposition='outside',
                           hovertemplate='<b>%{y}</b><br>暴露度: %{x:.3f}<br>预警等级: %{customdata}<extra></extra>',
                           customdata=industry_sorted['预警等级']))
    fig.update_layout(title="行业AI暴露度（全国平均）", xaxis_title="暴露度 (0-1)", yaxis_title="行业", height=650)
    st.plotly_chart(fig, use_container_width=True)
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f'<span class="warning-red">🔴 红色预警</span> 暴露度 > {q75:.2f}', unsafe_allow_html=True)
    with col2:
        st.markdown(f'<span class="warning-orange">🟠 橙色预警</span> > {q50:.2f}', unsafe_allow_html=True)
    with col3:
        st.markdown(f'<span class="warning-yellow">🟡 黄色预警</span> > {q25:.2f}', unsafe_allow_html=True)
    with col4:
        st.markdown(f'<span class="warning-blue">🔵 蓝色安全</span> ≤ {q25:.2f}', unsafe_allow_html=True)

# ========== 功能3：地区风险面板（突出就业人数和预警等级） ==========
elif option == "🗺️ 地区风险面板":
    st.subheader("🗺️ 省份AI风险与就业结构分析")
    provinces = sorted(panel_df['province'].unique())
    selected_prov = st.selectbox("选择省份", provinces)
    latest_year = panel_df['year'].max()

    prov_data = panel_df[(panel_df['province'] == selected_prov) & (panel_df['year'] == latest_year)].copy()
    if prov_data.empty:
        st.warning(f"暂无 {selected_prov} 的数据")
    else:
        total_emp = prov_data['employment'].sum()
        if total_emp > 0:
            prov_data['emp_share'] = prov_data['employment'] / total_emp
            prov_data['weighted_exposure'] = prov_data['exposure'] * prov_data['emp_share']
            weighted_exposure = prov_data['weighted_exposure'].sum()
        else:
            prov_data['emp_share'] = 0
            prov_data['weighted_exposure'] = 0
            weighted_exposure = 0

        # 全国平均综合风险
        national_panel = panel_df[panel_df['year'] == latest_year]
        national_total_emp = national_panel['employment'].sum()
        national_weighted = (national_panel.groupby('industry')['exposure'].mean() *
                             national_panel.groupby('industry')['employment'].sum()).sum() / national_total_emp

        prov_level = warning_level(weighted_exposure)
        prov_color = color_map[prov_level]

        # 展示省份综合指标
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(
                f'<div class="metric-card"><h4>🏆 省份综合风险指数</h4><h2 style="color:{prov_color}">{weighted_exposure:.3f}</h2><p>{prov_level}</p></div>',
                unsafe_allow_html=True)
        with col2:
            st.markdown(
                f'<div class="metric-card"><h4>📈 全国平均综合风险</h4><h2>{national_weighted:.3f}</h2><p>对比基准</p></div>',
                unsafe_allow_html=True)
        with col3:
            diff = weighted_exposure - national_weighted
            trend = "高于" if diff > 0 else "低于"
            color_trend = "red" if diff > 0 else "green"
            st.markdown(
                f'<div class="metric-card"><h4>⚖️ 与全国对比</h4><h2 style="color:{color_trend}">{trend} {abs(diff):.3f}</h2><p>{selected_prov}的风险水平{trend}全国平均</p></div>',
                unsafe_allow_html=True)

        # 表格：突出就业人数和预警等级
        prov_data['预警等级'] = prov_data['exposure'].apply(warning_level)
        prov_data['预警标签'] = prov_data['预警等级'].apply(lambda x: f'<span class="{warning_style(x)}">{x}</span>')
        table_data = prov_data[['industry', 'exposure', 'employment', 'emp_share', '预警标签']].copy()
        table_data['emp_share'] = table_data['emp_share'].apply(lambda x: f"{x:.1%}")
        table_data.columns = ['行业', '暴露度(全国统一)', '就业人数(万人)', '就业占比', '预警等级']
        # 按就业人数降序排列，突出就业规模的行业
        table_data = table_data.sort_values('就业人数(万人)', ascending=False)
        st.markdown("### 📋 各行业就业结构及AI暴露度（按就业人数排序）")
        st.write(table_data.to_html(escape=False, index=False), unsafe_allow_html=True)

        # 柱状图：使用“风险贡献 = 暴露度 × 就业占比”，不同省份不同
        chart_data = prov_data.sort_values('weighted_exposure', ascending=True)
        fig = go.Figure(go.Bar(
            x=chart_data['weighted_exposure'],
            y=chart_data['industry'],
            orientation='h',
            marker_color=[color_map[lvl] for lvl in chart_data['预警等级']],
            text=chart_data['weighted_exposure'].round(4),
            textposition='outside',
            hovertemplate='<b>%{y}</b><br>风险贡献: %{x:.4f}<br>预警等级: %{customdata}<extra></extra>',
            customdata=chart_data['预警等级']
        ))
        fig.update_layout(title=f"{selected_prov} 各行业对综合风险的贡献（暴露度 × 就业占比）",
                          xaxis_title="风险贡献权重", yaxis_title="行业", height=600)
        st.plotly_chart(fig, use_container_width=True)

        # 饼图：红色预警行业就业占比
        high_risk_ind = prov_data[prov_data['exposure'] > q75]['industry'].tolist()
        if high_risk_ind and total_emp > 0:
            high_risk_emp = prov_data[prov_data['industry'].isin(high_risk_ind)]['employment'].sum()
            pie_data = pd.DataFrame(
                {'类别': ['红色预警行业', '其他行业'], '就业人数': [high_risk_emp, total_emp - high_risk_emp]})
            fig_pie = px.pie(pie_data, values='就业人数', names='类别', title=f"{selected_prov} 红色预警行业就业占比",
                             color_discrete_sequence=['#d32f2f', '#b0bec5'])
            st.plotly_chart(fig_pie, use_container_width=True)

        st.info(
            "💡 **解读**：行业暴露度（全国统一）基于职业任务属性，不随省份变化。省份综合风险指数 = Σ(暴露度 × 就业占比)。左侧条形图展示每个行业对综合风险的贡献，不同省份的条形长度因就业占比不同而差异明显。")

# ========== 功能4：预警面板 ==========
elif option == "⚠️ 预警面板":
    st.subheader("⚠️ 行业预警状态（基于全国平均暴露度）")
    red = industry_avg_national[industry_avg_national['预警等级'] == '红色预警']['industry'].tolist()
    orange = industry_avg_national[industry_avg_national['预警等级'] == '橙色预警']['industry'].tolist()
    yellow = industry_avg_national[industry_avg_national['预警等级'] == '黄色预警']['industry'].tolist()
    blue = industry_avg_national[industry_avg_national['预警等级'] == '蓝色安全']['industry'].tolist()

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### 🔴 红色预警行业（立即行动）")
        for i in red: st.error(f"⚠️ {i}")
        st.markdown("### 🟠 橙色预警行业（重点关注）")
        for i in orange: st.warning(f"🔔 {i}")
    with col2:
        st.markdown("### 🟡 黄色预警行业（关注趋势）")
        for i in yellow: st.info(f"📌 {i}")
        st.markdown("### 🔵 蓝色安全行业（常规监测）")
        for i in blue: st.success(f"✅ {i}")
    st.markdown("### 📊 完整预警列表（按暴露度降序）")
    st.dataframe(industry_avg_national[['industry', 'exposure', '预警等级']].sort_values('exposure', ascending=False))

# ========== 功能5：政策建议 ==========
elif option == "📝 政策建议":
    st.subheader("📝 针对性政策建议")
    red_list = industry_avg_national[industry_avg_national['预警等级'] == '红色预警']['industry'].tolist()
    orange_list = industry_avg_national[industry_avg_national['预警等级'] == '橙色预警']['industry'].tolist()
    yellow_list = industry_avg_national[industry_avg_national['预警等级'] == '黄色预警']['industry'].tolist()

    st.markdown("### 🔴 红色预警行业政策包")
    if red_list:
        st.markdown(f"**涉及行业**：{', '.join(red_list)}")
        with st.expander("📌 详细建议（点击展开）"):
            st.markdown(
                "**1. 紧急转岗培训计划**\n- 联合人社部门开设3-6个月数字技能、人际沟通培训。\n**2. 就业缓冲基金**\n- 对收入下降30%以上职工给予最长12个月临时补贴。\n**3. 产业引导**\n- 发展社区服务、养老护理等AI互补行业。\n**4. 动态监测**\n- 月度用工监测，提前预警。")
    else:
        st.success("当前无红色预警行业。")

    st.markdown("### 🟠 橙色预警行业政策包")
    if orange_list:
        st.markdown(f"**涉及行业**：{', '.join(orange_list)}")
        with st.expander("📌 详细建议（点击展开）"):
            st.markdown(
                "**1. 人机协作培训**\n- 推广AI辅助工具，提升协同管理能力。\n**2. 灵活就业支持**\n- 完善平台经济社保，允许失业金用于培训。\n**3. 教育调整**\n- 高校增加AI相关课程。")
    else:
        st.info("当前无橙色预警行业。")

    st.markdown("### 🟡 黄色预警行业政策包")
    if yellow_list:
        st.markdown(f"**涉及行业**：{', '.join(yellow_list)}")
        with st.expander("📌 详细建议（点击展开）"):
            st.markdown("**1. 预防性培训**\n- 开展AI素养讲座和线上学习。\n**2. 区域交流**\n- 东西部行业对口分享经验。")
    else:
        st.info("当前无黄色预警行业。")

    st.markdown("### 🌐 通用政策建议")
    with st.expander("📌 点击查看详细通用建议"):
        st.markdown(
            "- **教育改革**：强化编程、创造力、批判性思维。\n- **社保完善**：灵活就业者纳入失业保险，建立个人培训账户。\n- **区域差异化**：东部聚焦AI研发，中西部发展人机协作制造。\n- **企业激励**：AI培训费用50%补贴。")

st.sidebar.markdown("---")
st.sidebar.info("数据来源：O*NET + 中国劳动力面板数据\n模型版本：2026.04")
st.sidebar.markdown("---")
if st.sidebar.button("🔄 刷新数据"):
    st.cache_data.clear()
    st.success("缓存已清除，下次加载将重新读取数据。")