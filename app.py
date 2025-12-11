# max_value=2 代表「朋友」最多選 2 個
friend_count = st.number_input("攜帶朋友數量 (不含自己，上限2人)", min_value=0, max_value=2, value=0)

# ... 中間省略 ...

# 1. 系統先加你自己 (Count = 1)
new_entries.append({ ... "name": name_input ... })

# 2. 如果你有選朋友 (例如選 2)，系統會跑迴圈再加 2 個人
if friend_count > 0:
    for i in range(friend_count):
        # 加朋友...
