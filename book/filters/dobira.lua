-- 조판용 변환(PDF). EPUB에는 장면 구분 div와 판권 처리만 적용한다.
local is_latex = FORMAT:match("latex")
local stringify = pandoc.utils.stringify

local function tex_escape(s)
  return (s:gsub("\\", "\\textbackslash{}"):gsub("([#$%%&_{}])", "\\%1"):gsub("~", "\\textasciitilde{}"))
end

local in_colophon = false
local seen_story, seen_back, seen_front = false, false, false
local map_full_page = false
local story_date = nil
local current_chapter = nil

function Header(h)
  if h.level == 1 and h.classes:includes("chapter-title") then
    story_date = nil
    local chapter_text = stringify(h.content)
    current_chapter = tonumber(chapter_text:match("^(%d+)장"))
  end
  if not is_latex then return nil end
  if h.level == 1 and h.classes:includes("helper") and stringify(h.content) == "곰새코지 바다 지도" then
    map_full_page = true
    return pandoc.RawBlock("latex",
      "\\fullpageimage{images/pagefill/map.png}")
  end
  if h.level == 1 and h.classes:includes("chapter-title") then
    local text = stringify(h.content)
    local num, title = text:match("^(%d+장)%.%s*(.+)$")
    if not num then return nil end
    local chapter_no = tonumber(num:match("^(%d+)"))
    local art_no = tonumber(h.attributes["data-art"]) or chapter_no
    local img = string.format("images/pagefill/ch%02d.png", art_no)
    local page_img = string.format("images/pagefill/ch%02d-page.png", art_no)
    local pre = ""
    if not seen_story then seen_story = true; pre = "\\addtocontents{toc}{\\protect\\tocgroup{이야기}}" end
    return pandoc.RawBlock("latex", pre .. string.format("\\dobira{%s}{%s}{%s}{%s}", num, tex_escape(title), img, page_img))
  end
  if h.level == 1 and h.classes:includes("colophon") then
    in_colophon = true
    return pandoc.RawBlock("latex", "\\colophonstart")
  end
  if h.level == 1 and (h.classes:includes("backmatter") or h.classes:includes("helper")) then
    local pre = {}
    if h.classes:includes("helper") and not seen_front then seen_front = true
      table.insert(pre, pandoc.RawBlock("latex", "\\addtocontents{toc}{\\protect\\tocgroup{읽기 전에}}")) end
    if h.classes:includes("backmatter") and not seen_back then seen_back = true
      table.insert(pre, pandoc.RawBlock("latex", "\\addtocontents{toc}{\\protect\\tocgroup{책 뒤에}}")) end
    table.insert(pre, h); table.insert(pre, pandoc.RawBlock("latex", "\\backmatterstyle"))
    return pre
  end
  if h.level == 2 and stringify(h.content) == "정답" then
    return {pandoc.RawBlock("latex", "\\clearpage"), h}
  end
  return nil
end

-- 장 첫 줄의 날짜(인라인 코드 한 덩어리) → 작은 회색 날짜 줄
-- 장면 구분 ◇ → 쪽 끝에 홀로 남지 않게
function Para(p)
  if is_latex and map_full_page then
    map_full_page = false
    return {}
  end
  if #p.content == 1 and p.content[1].t == "Code" then
    local stamp = p.content[1].text
    local month, day = stamp:match("^(%d+)월%s*(%d+)일")
    if month and day then story_date = month .. "월 " .. day .. "일" end
    if is_latex then
      return pandoc.RawBlock("latex", "\\dateline{" .. tex_escape(stamp) .. "}")
    end
  end
  if #p.content == 1 and stringify(p) == "◇" then
    if is_latex then
      return pandoc.RawBlock("latex", "\\Needspace{4\\baselineskip}\\begin{center}◇\\end{center}\\nopagebreak")
    end
    return pandoc.Div({p}, pandoc.Attr("", {"scene-break"}))
  end
  return nil
end

-- 소리 모양(U-D-F 등)은 줄 끝에서 끊지 않는다 / 라틴 확장 문자는 대체 글꼴
function Str(s)
  if not is_latex then return nil end
  if s.text:match("^%d+,") or s.text:match("^%d+…") then
    return pandoc.RawInline("latex", "\\mbox{" .. tex_escape(s.text) .. "}")
  end
  if s.text:match("^[UDF]%-[UDF][%-UDF]*") then
    return pandoc.RawInline("latex", "\\mbox{" .. tex_escape(s.text) .. "}")
  end
  if s.text:find("[\195][\128-\191]") then   -- U+00C0~U+00FF (é 등)
    local out = s.text:gsub("([\195][\128-\191])", "{\\latinx %1}")
    return pandoc.RawInline("latex", out)
  end
  return nil
end

function Code(c)
  if not is_latex then return nil end
  if c.text:match("^%d+,") or c.text:match("^%d+[:%.]") or c.text:match("^[A-Za-z0-9_%.%-]+$") then
    return pandoc.RawInline("latex", "\\mbox{\\texttt{" .. tex_escape(c.text) .. "}}")
  end
  return nil
end

local chat_speakers = {
  ["danu_0101"] = true, ["채아"] = true, ["단우"] = true, ["고단우"] = true,
  ["하안"] = true, ["다원"] = true, ["탁 박사"] = true, ["봉 소장"] = true,
  ["구멍가게"] = true, ["바당지기"] = true, ["강덕수"] = true,
}

local function split_lines(s)
  local out = {}
  for line in (s .. "\n"):gmatch("(.-)\n") do
    out[#out + 1] = line:gsub("\r$", "")
  end
  return out
end

local function parse_message(line)
  local time, sender, body = line:match("^%s*%[(%d%d:%d%d)%]%s*([^:]+):%s*(.*)$")
  if sender then return { time = time, sender = sender, body = body } end
  sender, body = line:match("^%s*([^:|]+):%s+(.+)$")
  if sender then return { sender = sender, body = body } end
  return nil
end

local function display_time(time)
  if not time then return nil end
  local hour = tonumber(time:sub(1, 2))
  local minute = time:sub(4, 5)
  local label
  if hour < 5 then
    label = string.format("새벽 %s:%s", time:sub(1, 2), minute)
  elseif hour < 12 then
    label = string.format("오전 %d:%s", hour, minute)
  elseif hour < 18 then
    label = string.format("오후 %d:%s", hour == 12 and 12 or hour - 12, minute)
  else
    label = string.format("밤 %d:%s", hour - 12, minute)
  end
  if story_date then return story_date .. " " .. label end
  return label
end

local function app_notice(lines)
  local source = lines[1] and lines[1]:match("^귀 기울임%s*|%s*(.+)$")
  if not source or source == "연구소 메시지" or source == "지난주 리더보드" or source == "내 정보" then
    return nil
  end
  local title = "귀 기울임 · " .. source
  local body_lines = {}
  for i = 2, #lines do
    if lines[i]:match("%S") then body_lines[#body_lines + 1] = lines[i] end
  end
  if source == "축하합니다!" then
    title = "귀 기울임 · AI 음성 분석 자동 알림"
    table.insert(body_lines, 1, source)
  end
  local sender
  if source == "연구소 공식 메시지" and body_lines[1] then
    sender = body_lines[1]:match("^보낸 사람:%s*(.+)$")
    if sender then table.remove(body_lines, 1) end
  end
  return title, body_lines, sender
end

local function make_chat(lines)
  local title, start = nil, 1
  local first = lines[1] or ""
  if not parse_message(first) then
    if first == "곰새코지 마을방" then
      title = first
      start = 2
    elseif first == "6학년 단톡방" then
      title = "곰새코지 6학년 수다방"
      start = 2
    else
      local app_title = first:match("^귀 기울임%s*|%s*(.+)$")
      if app_title == "연구소 메시지" then
        title = "귀 기울임 · 연구소 메시지"
        start = 2
      end
    end
  end
  local messages, recognized = {}, title ~= nil
  for i = start, #lines do
    local line = lines[i]
    if line:match("%S") then
      local message = parse_message(line)
      if not message then return nil end
      messages[#messages + 1] = message
      if chat_speakers[message.sender] then recognized = true end
    end
  end
  if #messages == 0 or not recognized then return nil end
  if not title and (current_chapter == 1 or current_chapter == 2) then
    title = "곰새코지 6학년 수다방"
  end

  local groups = {}
  for _, message in ipairs(messages) do
    local prior = groups[#groups]
    if prior and prior.sender == message.sender and prior.time == message.time then
      prior.body[#prior.body + 1] = message.body
    else
      groups[#groups + 1] = {
        sender = message.sender, time = message.time, body = { message.body }
      }
    end
  end

  if is_latex then
    local out = { "\\begin{chatthread}" }
    if title then out[#out + 1] = "\\chatroomtitle{" .. tex_escape(title) .. "}" end
    for _, group in ipairs(groups) do
      local label = group.sender
      local when = display_time(group.time)
      if when then label = label .. " (" .. when .. ")" end
      local safe_body = {}
      for _, text in ipairs(group.body) do safe_body[#safe_body + 1] = tex_escape(text) end
      local body = table.concat(safe_body, "\\\\")
      out[#out + 1] = "\\chatbubble{" .. tex_escape(label) .. "}{" .. body .. "}"
    end
    out[#out + 1] = "\\end{chatthread}"
    return pandoc.RawBlock("latex", table.concat(out, "\n"))
  end

  local function html(s)
    return (s:gsub("&", "&amp;"):gsub("<", "&lt;"):gsub(">", "&gt;"):gsub('"', "&quot;"))
  end
  local out = { '<section class="chat-thread">' }
  if title then out[#out + 1] = '<div class="chat-room">' .. html(title) .. "</div>" end
  for _, group in ipairs(groups) do
    local label = group.sender
    local when = display_time(group.time)
    if when then label = label .. " (" .. when .. ")" end
    out[#out + 1] = '<div class="chat-bubble"><div class="chat-meta">' .. html(label) .. '</div><div class="chat-text">' .. html(table.concat(group.body, "\n")):gsub("\n", "<br/>") .. '</div></div>'
  end
  out[#out + 1] = "</section>"
  return pandoc.RawBlock("html", table.concat(out, "\n"))
end

local function make_app_notice(title, lines, sender)
  local safe_body = {}
  for _, line in ipairs(lines) do safe_body[#safe_body + 1] = tex_escape(line) end
  local body = table.concat(safe_body, "\\\\")
  if is_latex then
    if sender then
      return pandoc.RawBlock("latex", "\\appnoticefrom{" .. tex_escape(title) .. "}{" .. tex_escape(sender) .. "}{" .. body .. "}")
    end
    return pandoc.RawBlock("latex", "\\appnotice{" .. tex_escape(title) .. "}{" .. body .. "}")
  end
  local function html(s)
    return (s:gsub("&", "&amp;"):gsub("<", "&lt;"):gsub(">", "&gt;"):gsub('"', "&quot;"))
  end
  local sender_html = sender and '<div class="app-notice-sender">보낸 사람: ' .. html(sender) .. '</div>' or ""
  return pandoc.RawBlock("html", '<section class="app-notice"><div class="app-notice-title">' .. html(title) .. '</div><div class="app-notice-body">' .. sender_html .. html(table.concat(lines, "\n")):gsub("\n", "<br/>") .. '</div></section>')
end

function CodeBlock(cb)
  local lines = split_lines(cb.text)
  local title, notice_lines, sender = app_notice(lines)
  if title then return make_app_notice(title, notice_lines, sender) end
  local chat = make_chat(lines)
  if chat then return chat end
  if not is_latex then return nil end
  return pandoc.RawBlock("latex",
    "\\begin{Verbatim}[samepage=true,frame=single,framesep=2.5mm,rulecolor=\\color{gray},formatcom=\\logfont]\n"
    .. cb.text .. "\n\\end{Verbatim}")
end

function Div(d)
  if d.classes:includes("chapter-interlude") and is_latex then
    local art_no = tonumber(d.attributes["data-art"])
    if art_no then
      return pandoc.RawBlock("latex", string.format(
        "\\chapterartpage{images/pagefill/ch%02d-page.png}{images/pagefill/ch%02d.png}", art_no, art_no))
    end
  end
  if d.classes:includes("sticky-note") then
    local note_lines = {}
    for _, block in ipairs(d.content) do
      local line = stringify(block)
      if line ~= "" then note_lines[#note_lines + 1] = line end
    end
    if is_latex then
      local safe_lines = {}
      for _, line in ipairs(note_lines) do safe_lines[#safe_lines + 1] = tex_escape(line) end
      return pandoc.RawBlock("latex", "\\stickynote{" .. table.concat(safe_lines, "\\\\[1mm]") .. "}")
    end
    local safe_lines = {}
    for _, line in ipairs(note_lines) do
      safe_lines[#safe_lines + 1] = line:gsub("&", "&amp;"):gsub("<", "&lt;"):gsub(">", "&gt;")
    end
    local escaped = table.concat(safe_lines, "<br/>\n")
    return pandoc.RawBlock("html", '<aside class="sticky-note"><div class="sticky-note-text">' .. escaped .. '</div></aside>')
  end
  if d.classes:includes("art-slot") and is_latex then
    return pandoc.RawBlock("latex",
      "\\begin{center}\\fbox{\\parbox[c][120mm][c]{0.9\\linewidth}{\\centering\\color{gray}\\small 지도 그림이 들어갈 자리}}\\end{center}")
  end
  return nil
end

function Pandoc(doc)
  if is_latex and in_colophon then
    doc.blocks:insert(pandoc.RawBlock("latex", "\\colophonend"))
  end
  return doc
end
