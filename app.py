import streamlit as st
import os
import urllib.parse
from openai import OpenAI
from dotenv import load_dotenv
from pathlib import Path

load_dotenv(dotenv_path=Path(__file__).parent / ".env")

# ローカル: .env / Streamlit Cloud: st.secrets
try:
    api_key = st.secrets["OPENAI_API_KEY"]
except Exception:
    api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)

SYSTEM_PROMPT = """
あなたはMJスター（マイケルジャクソンダンスレッスン）の運営者・鈴木の代わりにメール返信を下書きするアシスタントです。

以下のテンプレートと文体を参考に、受け取った問い合わせ内容に合わせて最適化した返信を作成してください。

【文体のルール】
- 丁寧かつフレンドリーなトーン
- 「〇〇様」から始める（差出人名がわかる場合）
- 「MJスター運営の鈴木」として署名（最後に「どうぞよろしくお願いいたします。\nMJスター運営 鈴木」を付ける）
- 問い合わせの内容（曲名・年齢・グループかプライベートか等）を汲み取って返信をカスタマイズ

【テンプレートパターンと使い分け】

①問い合わせ初回返信（基本形）
→ 新規問い合わせ全般。

【特定のレッスンに言及がない場合】（「レッスンに興味がある」「参加したい」など曲名・内容が指定されていない場合）
→ 現在開催中のレッスンを**全て**列挙し、「ご希望のレッスンはございますでしょうか？」と聞く。
レッスン日程情報から直近の開催予定を整理して、以下のように案内する：
例文：
「〇〇様、はじめまして。MJスター運営の鈴木と申します。この度はお問い合わせいただき誠にありがとうございます。
現在以下のレッスンを開催しております。

■〔レッスン名①〕
講師：〔講師名〕
次回：〔日時〕 〔スタジオ〕
料金：〔料金〕

■〔レッスン名②〕
講師：〔講師名〕
次回：〔日時〕 〔スタジオ〕
料金：〔料金〕

ご希望のレッスンはございますでしょうか？
また、講師のご希望等もございましたらお気軽にお知らせください。」

【特定のレッスン・曲名に言及がある場合】
→ そのレッスンの情報に絞って次回日程を案内する。

②レッスン詳細案内（申込確定後）
→ 参加意思が確認できたとき。スタジオ住所などの詳細を送る。
スタジオ情報：スタジオワークル原宿 108室、東京都渋谷区千駄ヶ谷3-53-2 BIZ原宿 B1、JR原宿駅 竹下口 徒歩6分

③当日リマインド
→ レッスン当日の朝に送る。集合場所を案内する。
例文：「本日はよろしくお願いします！到着されましたら地下一階にロビーがありますのでそちらにお越しください！」

④プライベートレッスン問い合わせ返信
→ 個人レッスン希望。まず踊りたい曲を聞く。
例文：「是非、お力添えさせていただきたく思います。ダンスをマスターしたい楽曲などはございますでしょうか？」

⑤子ども参加お断り
→ 概ね10歳以下の子どもの参加依頼。丁寧にお断り。
以下の文言を**必ず一字一句そのまま**含めること：
「せっかくお越しいただいたにもかかわらず、十分にお楽しみいただけないことが多かったため、現在は10歳以上のお子様を対象にレッスンを行っております。
ご期待に沿えず誠に申し訳ございません。」

⑥LINEグループ招待（参加確定後）
→ 参加が決まった方にLINEグループへの参加を促す。

⑦連絡遅延お詫び
→ 返信が遅れてしまった場合に必ずお詫びを入れる。
遅れた理由の例：「週末にダンスイベントに出演しておりました」「現在お問い合わせが殺到しております」

⑧最終回間近のレッスンへの参加案内（重要）
→ レッスン日程情報が提供されており、残り回数が少ない（目安：残り1〜2回）場合に使用。
ポイント：
- 「〔曲名〕ですが残り〇回となっており」と残り回数を明示する
- 「細かい振り付け指導はできない部分もございますが、動画撮影等でカバーいたしますので、その点ご了承いただけますと幸いです」という文言を必ず入れる
- 次のレッスンシリーズ（新曲）からの参加を勧める案内も添える
例文：
「〔曲名〕ですが残り〇回となっており、細かい振り付け指導はできない部分もございますが、
動画撮影等でカバーいたしますので、その点ご了承いただけますと幸いです。
もし最初から振り付けをしっかりと覚えたい場合は、次の曲が始まる基礎レッスンからのご参加がおすすめです。
次回は〔時期〕頃を予定しております。」

【重要な情報】
- スタジオ：スタジオワークル原宿 108室（上記参照）
- 講師：TATSUYA、Joy J、Rintaroなど（問い合わせの文脈から判断）
- 返信が遅れている場合は必ずお詫びを入れる
- 現在進行中の曲・次の曲が問い合わせ内容やレッスン日程情報に含まれていれば、それに合わせた案内をする
- レッスン日程情報が提供された場合は、その情報を活用して具体的な日程・残り回数を返信に盛り込む

返信文のみを出力してください（件名・「---」などの区切りは不要）。
"""


def generate_reply(inquiry_text: str, sender_name: str = "", schedule_info: str = "") -> str:
    schedule_section = f"\nレッスン日程情報:\n{schedule_info}" if schedule_info.strip() else ""
    user_prompt = f"""差出人名: {sender_name if sender_name else "（不明）"}

問い合わせ内容:
{inquiry_text}{schedule_section}
"""
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.3,
    )
    return response.choices[0].message.content


def gmail_compose_url(to: str, subject: str, body: str) -> str:
    params: dict[str, str] = {"view": "cm"}
    if to:
        params["to"] = to
    if subject:
        params["su"] = subject
    if body:
        params["body"] = body
    return "https://mail.google.com/mail/?" + urllib.parse.urlencode(params)


# ── UI ──────────────────────────────────────────────
st.set_page_config(page_title="MJスター 返信ジェネレーター", page_icon="🕺", layout="centered")
st.title("🕺 MJスター 問い合わせ返信ジェネレーター")
st.caption("問い合わせ内容を貼り付けると、テンプレを参考に最適化した返信を自動生成します")

# セッション状態で生成結果を保持
if "generated_reply" not in st.session_state:
    st.session_state.generated_reply = ""
if "last_email" not in st.session_state:
    st.session_state.last_email = ""
if "last_subject" not in st.session_state:
    st.session_state.last_subject = ""

FIXED_SUBJECT = "【MJスター運営】お問合せありがとうございます。"

DEFAULT_SCHEDULE = """\
【日曜レッスン】
7/5(日)  スリラー(TATSUYA) 13:00-14:30 スタジオワークル原宿108
7/12(日) MJ基礎 13:00-14:30 スタジオワークル原宿108 / ビートイット 15:30-17:00 スタジオワークル原宿108→109
7/19(日) スリラー(TATSUYA) 13:30-15:00 ★最終・撮影会 BUZZ池袋東口BASE 1スタジオ
7/26(日) 休み
8/2(日)  MJ基礎 13:00-14:30 ★最終・撮影会 buzz渋谷TOWER / ビートイット 15:00-16:30 ★最終・撮影会 buzz渋谷TOWER
8/9(日)  TATSUYAレッスン(曲未定) 13:00-14:30 ← 新シリーズ開始
8/16(日) MJ基礎(曲未定) 13:00-14:30 / Rintaroレッスン(曲未定) 15:30-17:00 ← 新シリーズ開始

【土曜・平日レッスン】
7/6  ビリージーン？
7/13 基礎固め
7/20 スムクリ 13:30-15:00 スタジオワークル原宿109 / デンジャ 15:30-17:00 スタジオワークル原宿109
7/26 うらしさまレッスン 16:00
7/27 基礎固め
8/3  スムクリ 13:30-15:00 スタジオワークル原宿301 / デンジャ 15:30-17:00 スタジオワークル原宿103
8/10 マイケル基礎 13:00-14:00 + 基礎固め スタジオワークル原宿104 / うらしさん buzz新宿 16:00
8/17 スムクリ 13:30-15:00 スタジオワークル原宿301 / デンジャ 15:30-17:00 スタジオワークル原宿103
8/24 マイケル基礎 13:00-14:00 + 基礎固め スタジオワークル原宿104
8/31 スムクリ 13:30-15:00 スタジオワークル原宿301 / デンジャ 15:30-17:00 スタジオワークル原宿103
9/7  スムクリ 13:30-15:00 未定 / デンジャ 15:30-17:00 未定
9/14 マイケル基礎 13:00-14:00 + 基礎固め 未定
9/21 スムクリ 13:30-15:00 未定 / デンジャ 15:30-17:00 未定
9/28 マイケル基礎 13:00-14:00 + 基礎固め 未定 / デンジャ 15:30-17:00 未定
"""

with st.form("form"):
    col1, col2 = st.columns(2)
    with col1:
        sender_name = st.text_input("差出人名（任意）", placeholder="例：山田 太郎")
    with col2:
        sender_email = st.text_input("返信先メール（任意）", placeholder="例：yamada@example.com")

    subject = st.text_input("件名", value=FIXED_SUBJECT)

    inquiry = st.text_area(
        "問い合わせ内容を貼り付け *",
        height=180,
        placeholder="受け取った問い合わせメールの本文をここに貼り付けてください...",
    )

    schedule_info = st.text_area(
        "直近のレッスン日程 — 残り回数が少ない場合は自動で注意文を追加します（更新時はここを編集）",
        value=DEFAULT_SCHEDULE,
        height=200,
    )

    submitted = st.form_submit_button("✨ 返信を生成する", use_container_width=True, type="primary")

if submitted:
    if not inquiry.strip():
        st.warning("問い合わせ内容を入力してください。")
        st.session_state.generated_reply = ""
    else:
        with st.spinner("返信を生成中..."):
            reply = generate_reply(inquiry, sender_name, schedule_info)
        st.session_state.generated_reply = reply
        st.session_state.last_email = sender_email
        st.session_state.last_subject = subject

# 生成結果を表示（セッション状態から）
if st.session_state.generated_reply:
    st.success("返信が生成されました！内容を確認・編集してから保存してください。")

    edited_reply = st.text_area(
        "生成された返信（編集可能）",
        value=st.session_state.generated_reply,
        height=320,
        key="reply_area",
    )

    gmail_url = gmail_compose_url(
        st.session_state.last_email,
        st.session_state.last_subject,
        edited_reply,
    )
    st.link_button(
        "📧 Gmailで開いて下書き保存する",
        gmail_url,
        use_container_width=True,
        type="primary",
    )
    st.caption("ボタンを押すとGmailの作成画面が開きます。内容を確認して「下書き保存」をクリックしてください。")

    if st.button("🔄 リセット（新しい問い合わせ）", use_container_width=True):
        st.session_state.generated_reply = ""
        st.rerun()
