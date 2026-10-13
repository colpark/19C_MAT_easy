# Render brief (V6-3)
Write a readable trace of one execution log, following the rules in `v6/spec/render_template.md` exactly.
Read only these files: the log you are given (`v6/exemplar/render/gold_A_log.json` or `gold_B_log.json`), `v6/spec/graph_R.json`,
and `v6/spec/render_template.md`. Do not read any other file. Use only numbers that appear in the log or its constants, at the
precision shown (write small counts as words). Name nodes by their graph ids. Plain sentences, active voice, no semicolons, no dashes
as punctuation. The validation suite has not run yet, so the closing "Why each step matters" paragraph states what each test will
check, without numbers or results. Write the text to `v6/exemplar/render/gold_A.md` (and `gold_B.md`). Do not edit the log.
