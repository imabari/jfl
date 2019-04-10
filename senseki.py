import pandas as pd

dfs = pd.read_html(
    'http://www.jfl.or.jp/jfl-pc/view/s.php?a=1411&f=2019A001_spc.html',
    skiprows=1,
    na_values='-')

jfl_2019 = [
    'Ｈｏｎｄａ ＦＣ', 'ＦＣ大阪', 'ソニー仙台ＦＣ', 'ＦＣ今治', '東京武蔵野シティＦＣ', 'ＭＩＯびわこ滋賀', '奈良クラブ',
    'ヴェルスパ大分', 'ラインメール青森', 'ヴィアティン三重', 'テゲバジャーロ宮崎', 'ＦＣマルヤス岡崎', 'ホンダロックＳＣ',
    '流経大ドラゴンズ龍ケ崎', '松江シティＦＣ', '鈴鹿アンリミテッド'
]

len(dfs)

df = pd.concat(
    dfs, keys=[i for i in range(1,
                                len(dfs) + 1)], names=['節', '番号'])
df.columns = ['日にち', '時間', 'ホーム', 'スコア', 'アウェイ', 'スタジアム', '備考']
df.drop('備考', axis=1, inplace=True)
df.head(10)

# 欠損値確認
df[df.isnull().any(axis=1)]

# スコアがないものを除去
df1 = df.dropna(subset=['スコア'])

# スコアを分割、スコアを削除、結合
df2 = pd.concat(
    [df1, df1['スコア'].str.split('-', expand=True)], axis=1).drop(
        'スコア', axis=1)

# 名前をホーム得点、アウェイ得点に変更
df2.rename(columns={0: 'ホーム得点', 1: 'アウェイ得点'}, inplace=True)

# ホーム得点、アウェイ得点を文字から整数に変更
df2['ホーム得点'] = df2['ホーム得点'].astype(int)
df2['アウェイ得点'] = df2['アウェイ得点'].astype(int)
df2.dtypes

# ホームの結果のみ
df_home = df2.loc[:, ['ホーム', 'アウェイ', 'ホーム得点', 'アウェイ得点']].reindex()
df_home.columns = ['チーム名', '対戦相手', '得点', '失点']
df_home['戦'] = 'H'
df_home.head()

# アウェイの結果のみ
df_away = df2.loc[:, ['アウェイ', 'ホーム', 'アウェイ得点', 'ホーム得点']]
df_away.columns = ['チーム名', '対戦相手', '得点', '失点']
df_away['戦'] = 'A'
df_away.head()

# ホームとアウェイを結合
df_total = pd.concat([df_home, df_away])

df_total.head()


# 勝敗を追加
def win_point(x):
    if x['得点'] > x['失点']:
        return '{}○{}'.format(x['得点'], x['失点'])
    elif x['得点'] < x['失点']:
        return '{}●{}'.format(x['得点'], x['失点'])
    else:
        return '{}△{}'.format(x['得点'], x['失点'])


df_total['勝敗'] = df_total.apply(lambda x: win_point(x), axis=1)
df_total

# 得点・失点・得失点・勝点　集計
pv_score = df_total.pivot_table(
    values='勝敗',
    index=['チーム名', '戦'],
    columns='対戦相手',
    aggfunc=sum,
    fill_value='')

new_idx = pd.MultiIndex.from_product(
    [jfl_2019, ['H', 'A']], names=pv_score.index.names)
score = pv_score.reindex(new_idx, columns=jfl_2019)
score.fillna('', inplace=True)
score

score.to_excel('2019_senseki.xlsx', sheet_name='戦績表')
