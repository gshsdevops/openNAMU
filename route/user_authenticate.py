from .tool.func import *
from route.tool.func_mail import *
import hashlib;

def user_authenticate():
    with get_db_connect() as conn:
        curs = conn.cursor()

        support_language = ['default'] + get_init_set_list()['language']['list']
        
        ip = ip_check()

        if ip_or_user(ip) == 0:
            if flask.request.method == 'POST':
                # 여기에서는 gsmail이 gs.hs.kr 메일이 맞는지 확인 후
                # 맞다면 메일을 보낸다.
                # 메일은 /authenticate/<hash> 링크를 보낸다.
                # hash는 단방향 해시를 하고, 내용은 os.environ['OpenNAMUSalt'] + (아이디 길이): + 아이디 + (메일 주소 길이): + 메일 주소
                curs.execute(db_change('select data from user_set where name = "user_name" and id = ?'), [ip])
                db_data = curs.fetchall()
                user_name = db_data[0][0] if db_data else ip

                address = flask.request.form.get('gsmail', '');

                if not address.endswith("@gs.hs.kr"):
                    # gs.hs.kr 메일이 아니다.
                    flask.session['error'] = load_lang('wrongaccount');
                    return redirect("/authenticate");

                hs = os.environ['OpenNAMUSalt'] + str(len(user_name)) + ':' + user_name + str(len(address)) + ':' + address

                url = f"http://cslab.gs.hs.kr/authenticate?hash={hashlib.sha256(hs.encode('utf-8')).hexdigest()}&address={address}";

                custom_send_email(address, "GSHS Wiki 계정을 인증하십시오", name = user_name, id = os.urandom(4).hex(), url = url);
                return redirect('/change');
            elif not flask.request.args.get('hash') or not flask.request.args.get('address'):
                curs.execute(db_change('select data from user_set where name = "email" and id = ?'), [ip])
                data = curs.fetchall()
                email = data[0][0] if data and data[0][0] != '' else '-'

                curs.execute(db_change('select data from user_set where name = "random_key" and id = ?'), [ip])
                data = curs.fetchall()
                ramdom_key = data[0][0] if data and data[0][0] != '' else '-'

                curs.execute(db_change('select data from user_set where name = "skin" and id = ?'), [ip])
                data = curs.fetchall()
                div2 = load_skin(data[0][0] if data else '', 0, 1)

                curs.execute(db_change('select data from user_set where name = "lang" and id = ?'), [ip])
                data = curs.fetchall()
                data = [['default']] if not data else data
                div3 = ''
                for lang_data in support_language:
                    see_data = lang_data if lang_data != 'default' else load_lang('default')

                    if data and data[0][0] == lang_data:
                        div3 = '<option value="' + lang_data + '">' + see_data + '</option>' + div3
                    else:
                        div3 += '<option value="' + lang_data + '">' + see_data + '</option>'

                # 여기 잘못 짬
                curs.execute(db_change('select data from user_set where name = "user_title" and id = ?'), [ip])
                data = curs.fetchall()
                data = [['']] if not data else data
                user_title_list = get_user_title_list()
                
                curs.execute(db_change('select data from user_set where name = "user_name" and id = ?'), [ip])
                db_data = curs.fetchall()
                user_name = db_data[0][0] if db_data else ip

                curs.execute(db_change('select data from user_set where name = "sub_user_name" and id = ?'), [ip])
                db_data = curs.fetchall()
                sub_user_name = db_data[0][0] if db_data else ''

                error = '';
                if 'error' in flask.session:
                    error = flask.session['error'];
                    del flask.session['error']

                return easy_minify(flask.render_template(skin_check(),
                    imp = [load_lang('user_setting'), wiki_set(), wiki_custom(), wiki_css([0, 0])],
                    data = f'''
                        <form method="post">
                            <span>gs.hs.kr 메일 입력</span>
                            <input name="gsmail"></input><br>
                            <span style="color: red;">{error}</span>
                            <hr class="main_hr">
                            <button type="submit">''' + load_lang('authenticate') + '''</button>
                            ''' + http_warning() + '''
                        </form>
                    ''',
                    menu = [['user', load_lang('return')]]
                ))
            else:
                # 링크를 클릭하면 다음을 확인
                # OpenNAMUSalt 값이 일치하는지
                # 로그인된 아이디가 일치하는지
                # 이미 인증된 계정이 없는지
                # 그 후 아이디에 메일 주소를 연결한다.
                curs.execute(db_change('select data from user_set where name = "user_name" and id = ?'), [ip])
                db_data = curs.fetchall()
                user_name = db_data[0][0] if db_data else ip

                address = flask.request.args.get('address');

                hs = os.environ['OpenNAMUSalt'] + str(len(user_name)) + ':' + user_name + str(len(address)) + ':' + address;
                if hashlib.sha256(hs.encode('utf-8')).hexdigest() != flask.request.args.get('hash'):
                    return re_error('/error/0');

                curs.execute(db_change('select data from user_set where name = "linked" and id = ?'), [ip])
                data = curs.fetchall()
                linked = data[0][0] if data and data[0][0] != '' else None

                if linked != None:
                    return re_error('/error/0');

                curs.execute(db_change('select data from user_set where name = "linked" and data = ?'), [address])
                data = curs.fetchall()
                linked = data[0][0] if data and data[0][0] != '' else None

                if linked != None:
                    return re_error('/error/0');

                curs.execute(db_change('insert into user_set (name, id, data) values ("linked", ?, ?)'), [ip, address])
                data = curs.fetchall()

                return redirect('/change');
        elif flask.request.args.get('hash') == '' or flask.request.args.get('address') == '':
            return redirect('/change')
        else:
            return re_error('/error/1');
