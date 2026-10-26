
                reply_markup=main_reply_kb() if not AVAILABLE_IMG
                else _status_with_imggen_kb(user["imggen"]))
        return

    if text == BTN_CANCEL:
        set_state(uid, "chat")
        bot.send_message(uid, "↩️ Отменено.", reply_markup=main_reply_kb()); return

    if text.startswith("/"): return

    state = get_state(uid)
    if state == "img_wait":
        set_state(uid, "chat")
        threading.Thread(target=do_imagine, args=(uid, text), daemon=True).start()
        return

    threading.Thread(target=do_chat, args=(uid,), kwargs={"text": text}, daemon=True).start()

def _status_with_imggen_kb(current_ig):
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(InlineKeyboardButton("🎨 Сменить генератор фото", callback_data="show_imggen"))
    return kb

# ── Файлы ─────────────────────────────────────────────────────────
def _file_thread(message, file_id, forced_mime=None):
    uid = message.chat.id
    try:
        if message.document and (message.document.file_size or 0) > MAX_FILE_MB*1024**2:
            bot.send_message(uid, f"❌ Файл больше {MAX_FILE_MB} МБ."); return
        bot.send_chat_action(uid, "upload_document")
        fdata, fmime = tg_dl(file_id)
        if forced_mime: fmime = forced_mime
        caption = getattr(message, "caption", "") or ""
        if fmime == "text/plain":
            do_chat(uid, text=(caption+"\n\n[TXT]:\n"+fdata.decode("utf-8","replace")[:14000]).strip())
            return
        do_chat(uid, text=caption, fdata=fdata, fmime=fmime)
    except Exception as e:
        bot.send_message(uid, "❌ Не удалось загрузить файл.")

@bot.message_handler(content_types=["photo"])
def h_photo(m):
    threading.Thread(target=_file_thread,
        args=(m, m.photo[-1].file_id, "image/jpeg"), daemon=True).start()

@bot.message_handler(content_types=["document"])
def h_doc(m):
    doc = m.document; mime = doc.mime_type or ""
    fname = (doc.file_name or "").lower()
    if fname.endswith(".docx"): mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    elif fname.endswith(".txt"): mime="text/plain"
    if mime not in _SUPPORTED:
        bot.send_message(m.chat.id, "❌ Поддерживаются: PDF, DOCX, TXT, PNG, JPG, WEBP"); return
    threading.Thread(target=_file_thread, args=(m, doc.file_id), daemon=True).start()

# ── Callbacks ─────────────────────────────────────────────────────
@bot.callback_query_handler(func=lambda c: c.data.startswith("cat:"))
def cb_cat(call):
    cat = call.data.split(":",1)[1]
    bot.answer_callback_query(call.id)
    if cat == "back":
        try:
            bot.edit_message_text("🤖 Выбери категорию:",
                call.message.chat.id, call.message.message_id,
                reply_markup=categories_kb())
        except: pass
        return
    user = get_user(call.from_user.id)
    em, label = CATEGORIES.get(cat, ("",""))
    try:
        bot.edit_message_text(
            f"{em} <b>{label}</b> — выбери модель:",
            call.message.chat.id, call.message.message_id,
            reply_markup=models_in_cat_kb(cat, user["model"]))
    except: pass

@bot.callback_query_handler(func=lambda c: c.data.startswith("mdl:"))
def cb_mdl(call):
    mkey = call.data.split(":",1)[1]
    if mkey not in AVAILABLE:
        bot.answer_callback_query(call.id, "❌ Модель недоступна"); return
    set_model(call.from_user.id, mkey)
    m = MODELS[mkey]
    bot.answer_callback_query(call.id, f"✅ {m['name']}")
    try:
        bot.edit_message_text(
            f"✅ {m['emoji']} <b>{m['name']}</b>",
            call.message.chat.id, call.message.message_id)
    except: pass

@bot.callback_query_handler(func=lambda c: c.data.startswith("img:"))
def cb_img(call):
    ikey = call.data.split(":",1)[1]
    if ikey not in AVAILABLE_IMG:
        bot.answer_callback_query(call.id, "❌ Недоступно"); return
    set_imggen(call.from_user.id, ikey)
    m = IMGGEN[ikey]
    bot.answer_callback_query(call.id, f"✅ {m['name']}")
    try:
        bot.edit_message_text(f"✅ {m['emoji']} <b>{m['name']}</b>",
            call.message.chat.id, call.message.message_id)
    except: pass

@bot.callback_query_handler(func=lambda c: c.data == "show_imggen")
def cb_show_img(call):
    bot.answer_callback_query(call.id)
    user = get_user(call.from_user.id)
    try:
        bot.edit_message_text("🎨 Выбери генератор:",
            call.message.chat.id, call.message.message_id,
            reply_markup=imggen_kb(user["imggen"]))
    except: pass

@bot.callback_query_handler(func=lambda c: c.data.startswith("regen:"))
def cb_regen(call):
    bot.answer_callback_query(call.id, "🔄 Генерирую…")
    threading.Thread(target=do_imagine, args=(call.from_user.id, call.data[6:]),
                     daemon=True).start()

@bot.callback_query_handler(func=lambda c: c.data == "new_prompt")
def cb_new_prompt(call):
    b
            text  = str(body.get("text","")).strip()
            model = body.get("model")
            if uid and text:
                threading.Thread(target=do_chat, daemon=True,
                    kwargs={"uid":uid,"text":text,"api_model":model}).start()
                resp = {"status":"queued"}
            else: resp = {"status":"error","detail":"chat_id and text required"}
        except Exception as e: resp = {"status":"error","detail":str(e)}
        self.send_response(200)
        self.send_header("Content-Type","application/json"); self.end_headers()
        self.wfile.write(json.dumps(resp).encode())
    def log_message(self,*a): pass

def _start_api(port):
    try:
        HTTPServer(("127.0.0.1", port), _APIHandler).serve_forever()
    except Exception as e: print(f"⚠️ HTTP API: {e}")


# ══════════════════════════════════════════════════════════════════
#   ЗАПУСК
# ══════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    print("="*54)
    print("  AI BOT v4.0  —  17+ моделей · чистый UX · админка")
    print("="*54)
    print(f"Доступно моделей: {len(AVAILABLE)}")
    for cat_id, (em,label) in CATEGORIES.items():
        mods = [v["name"] for v in AVAILABLE.values() if v["category"]==cat_id]
      