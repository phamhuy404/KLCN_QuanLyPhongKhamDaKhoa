import sys

filepath = 'controllers/admin_controller.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

def robust_replace(src, find_str, rep_str):
    if find_str in src:
        return src.replace(find_str, rep_str), True
    find_crlf = find_str.replace('\r\n', '\n').replace('\n', '\r\n')
    rep_crlf = rep_str.replace('\r\n', '\n').replace('\n', '\r\n')
    if find_crlf in src:
        return src.replace(find_crlf, rep_crlf), True
    return src, False

old_call = """        work_stats=ScheduleModel.get_work_statistics_and_history(
            current_user=curr_user,
            selected_month=request.args.get('stats_month'),
            scope=request.args.get('stats_scope'),
            filter_staff_id=request.args.get('stats_staff_id')
        )"""

new_call = """        work_stats=ScheduleModel.get_work_statistics_and_history(
            current_user=curr_user,
            selected_month=request.args.get('stats_month'),
            scope=request.args.get('stats_scope'),
            filter_staff_id=request.args.get('stats_staff_id'),
            filter_dept_id=request.args.get('stats_dept_id'),
            filter_role=request.args.get('stats_role'),
            search_keyword=request.args.get('stats_search')
        )"""

content, ok = robust_replace(content, old_call, new_call)
print("Updated admin_controller.py call:", ok)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
print("Done!")
