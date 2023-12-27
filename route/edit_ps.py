from .tool.func import *

def edit_render_set(name, content):
    render_set(
        doc_name = name,
        doc_data = content
    )

# https://stackoverflow.com/questions/13821156/timeout-function-using-threading-in-python-does-not-work
def edit_timeout(func, args = (), timeout = 3):
    pool = multiprocessing.Pool(processes = 1)
    result = pool.apply_async(func, args = args)
    try:
        result.get(timeout = timeout)
    except multiprocessing.TimeoutError:
        pool.terminate()
        return 1
    else:
        pool.close()
        pool.join()
        return 0
        
def edit_editor(curs, ip, data_main = '', publicity = False):
    return '''
        <select name="publicity">
            <option value="public"''' + (' selected' if publicity == False else '') + '''>공개</option>
            <option value="private"''' + (' selected' if publicity != False else '') + '''>비공개</option>
        </select>
    '''

def edit_ps(name = 'Test', section = 0, do_type = ''):
    with get_db_connect() as conn:
        curs = conn.cursor()
    
        ip = ip_check()

        if ip_or_user(ip) == 0:
            if acl_check(name, 'document_edit') == 1:
                return redirect('/raw_acl/' + url_pas(name))
            
            if do_title_length_check(name) == 1:
                return re_error('/error/38')
            
            curs.execute(db_change("select id from history where title = ? order by id + 0 desc"), [name])
            doc_ver = curs.fetchall()
            doc_ver = doc_ver[0][0] if doc_ver else '0'
            
            post_ver = flask.request.form.get('ver', '')
            if flask.request.method == 'POST':
                edit_repeat = 'error' if post_ver != doc_ver else 'post'
            else:
                edit_repeat = 'get'
            
            if edit_repeat == 'post':
                if captcha_post(flask.request.form.get('g-recaptcha-response', flask.request.form.get('g-recaptcha', ''))) == 1:
                    return re_error('/error/13')
                else:
                    captcha_post('', 0)
        
                if do_edit_slow_check() == 1:
                    return re_error('/error/24')

                curs.execute(db_change('select data from user_set where name = "linked" and id = ?'), [ip])
                data = curs.fetchall()
                linked = data[0][0] if data and data[0][0] != '' else None

                if linked == None:
                    return redirect('/raw_acl/' + url_pas(name))
        
                today = get_time()
                curs.execute(db_change("select data from data where title = ?"), [name])
                db_data = curs.fetchall()
                data = db_data[0][0] if db_data else ''
                content = data.replace('\r', '')
                send = flask.request.form.get('send', '')
                agree = flask.request.form.get('copyright_agreement', '')
                publicity = flask.request.form.get('publicity', '')
                publicity = (True if publicity == 'private' else False)

                curs.execute(db_change("select set_data from data_set where doc_name = ? and set_name = 'publicity'"), [name])
                db_data = curs.fetchall()
                curr_publicity = db_data[0][0] if db_data else False
                curr_publicity = (True if curr_publicity != False else False)

                if curr_publicity == publicity:
                    return re_error('/error/0')

                if publicity:
                    curs.execute(db_change("insert into data_set (doc_name, set_name, set_data) values (?, 'publicity', 'true')"), [name])
                    db_data = curs.fetchall()
                else:
                    curs.execute(db_change("delete from data_set where doc_name = ? and set_name = 'publicity'"), [name])
                    db_data = curs.fetchall()
                
                if do_edit_filter(content) == 1:
                    return re_error('/error/21')

                if do_edit_send_check(send) == 1:
                    return re_error('/error/37')

                if do_edit_text_bottom_check_box_check(agree) == 1:
                    return re_error('/error/29')
                
                curs.execute(db_change("select data from data where title = ?"), [name])
                db_data = curs.fetchall()
                if db_data:
                    o_data = db_data[0][0].replace('\r', '')
        
                    leng = leng_check(len(o_data), len(content))
                else:
                    leng = '+' + str(len(content))

                curs.execute(db_change("select data from other where name = 'edit_timeout'"))
                db_data_2 = curs.fetchall()
                db_data_2 = '' if not db_data_2 else number_check(db_data_2[0][0])

                if db_data_2 != '' and platform.system() == 'Linux':
                    timeout = edit_timeout(edit_render_set, (name, content), timeout = int(db_data_2))
                else:
                    timeout = 0

                if timeout == 1:
                    return re_error('/error/41')
                
                if db_data:
                    curs.execute(db_change("update data set data = ? where title = ?"), [content, name])
                else:    
                    curs.execute(db_change("insert into data (title, data) values (?, ?)"), [name, content])
        
                    curs.execute(db_change('select data from other where name = "count_all_title"'))
                    curs.execute(db_change("update other set data = ? where name = 'count_all_title'"), [str(int(curs.fetchall()[0][0]) + 1)])
        
                curs.execute(db_change("select user from scan where title = ? and type = ''"), [name])
                for scan_user in curs.fetchall():
                    add_alarm(scan_user[0], ip, '<a href="/w/' + url_pas(name) + '">' + html.escape(name) + '</a>')
                        
                history_plus(
                    name,
                    content,
                    today,
                    ip,
                    send,
                    leng
                )
                
                curs.execute(db_change("delete from back where link = ?"), [name])
                curs.execute(db_change("delete from back where title = ? and type = 'no'"), [name])
                
                render_set(
                    doc_name = name,
                    doc_data = content,
                    data_type = 'backlink'
                )
                
                conn.commit()
                
                return redirect('/w/' + url_pas(name))
            else:
                doc_section_edit_apply = 'X'
                data_section = ''
                data_section_where = ''

                if edit_repeat == 'get':
                    if do_type == 'load':
                        if flask.session and 'edit_load_document' in flask.session:
                            load_title = flask.session['edit_load_document']
                        else:
                            load_title = 0
                    else:
                        load_title = 0
                    
                    if load_title == 0:
                        load_title = name
                        
                    curs.execute(db_change("select data from data where title = ?"), [load_title])
                    db_data = curs.fetchall()
                    data = db_data[0][0] if db_data else ''
                    data = data.replace('\r', '')

                else:
                    curs.execute(db_change("select data from data where title = ?"), [load_title])
                    db_data = curs.fetchall()
                    data = db_data[0][0] if db_data else ''
                    data = data.replace('\r', '')
                    
                    data_section_where = flask.request.form.get('doc_section_data_where', '')
                    doc_section_edit_apply = flask.request.form.get('doc_section_edit_apply', '')

                    doc_ver = flask.request.form.get('ver', '')

                if data_section == '':
                    data_section = data

                form_action = 'formaction="/ps/' + url_pas(name) + '"'

                curs.execute(db_change("select set_data from data_set where doc_name = ? and set_name = 'publicity'"), [name])
                db_data = curs.fetchall()
                publicity = db_data[0][0] if db_data else False

                return easy_minify(flask.render_template(skin_check(), 
                    imp = [name, wiki_set(), wiki_custom(), wiki_css(['(' + load_lang('publicity') + ')', 0])],
                    data = '''
                        <form method="post">
                            <textarea style="display: none;" name="doc_section_data_where">''' + data_section_where + '''</textarea>
                            <input style="display: none;" name="doc_section_edit_apply" value="''' + doc_section_edit_apply + '''">

                            <input style="display: none;" name="ver" value="''' + doc_ver + '''">
                            
                            ''' + edit_editor(curs, ip, data_section, publicity) + '''

                            <input placeholder="''' + load_lang('why') + '''" name="send">
                            <hr class="main_hr">
                            
                            ''' + captcha_get() + ip_warning() + get_edit_text_bottom_check_box() + get_edit_text_bottom() + '''
                            
                            <button id="opennamu_save_button" type="submit" ''' + form_action + ''' onclick="do_monaco_to_textarea(); do_stop_exit_release();">''' + load_lang('save') + '''</button>
                        </form>
                        
                        <hr class="main_hr">
                    ''',
                    menu = [
                        ['w/' + url_pas(name), load_lang('return')]
                    ]
                ))
            return;
        else:
            return re_error('/error/1');