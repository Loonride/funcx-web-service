from flask import (abort, Blueprint, current_app as app, flash, jsonify,
                   redirect, render_template, request, session, url_for)
import uuid
from gui.forms import EditForm
from models.utils import get_db_connection
from authentication.auth import authenticated

# Flask
guiapi = Blueprint("guiapi", __name__)


@guiapi.route('/')
def start():
    return render_template('start.html')


@guiapi.route('/debug')
def debug():
    session.update(
        username='ryan@globusid.org'
    )
    return jsonify({'username': session.get("username")})


@guiapi.route('/home')
# @authenticated
def home():
    return render_template('home.html', title='Home')


@guiapi.route('/404')
def error():
    return render_template('404.html', title='Error')


@guiapi.route('/functions')
#@authenticated
def functions():
    # functions = Function.query.order_by(Function.date_created).all()
    # length = len(functions)
    # numPages = ceil(length/12)
    try:
        conn, cur = get_db_connection()
        cur.execute("SELECT functions.id AS function_id, function_name, timestamp, modified_at "
                    "FROM functions, users "
                    "WHERE functions.user_id = users.id AND users.username = %s AND functions.deleted = False",
                    (session.get("username"),))
        functions = cur.fetchall()
        functions_total = len(functions)
        # print(functions)
        # func = functions[20]
        # print(func['functions.id'])
    except:
        flash('There was an issue handling your request', 'danger')
        return redirect(url_for('guiapi.home'))
    return render_template('functions.html', title='Your Functions', functions=functions, functions_total=functions_total)


def getUUID():
    return str(uuid.uuid4())


@guiapi.route('/new', methods=['GET', 'POST'])
# @authenticated
def new():

    # TODO (from Tyler) -- have this reroute to funcx.org/api/v1/register_function (rather than reinventing the wheel).
    # TODO: This request should contain: user_id, user_name, short_name
    # TODO: But talk to Ryan about this.

    form = EditForm()
    if form.validate_on_submit():
        name = form.name.data
        desc = form.desc.data
        entry_point = form.entry_point.data
        uuid = getUUID()
        code = form.code.data
        try:
            conn, cur = get_db_connection()
            cur.execute("INSERT INTO functions (function_name, description, entry_point, function_uuid, function_code) VALUES (%s, %s, %s, %s, %s)", (name, desc, entry_point, uuid, code))
            conn.commit()
            flash(f'Saved Function "{name}"!', 'success')
            # return redirect('../view/' + str(450))
            return redirect(url_for('guiapi.home'))
        except:
            flash('There was an issue handling your request', 'danger')
    return render_template('edit.html', title='New Function', form=form, cancel_route="functions")


@guiapi.route('/edit/<id>', methods=['GET', 'POST'])
# @authenticated
def edit(id):
    conn, cur = get_db_connection()
    cur.execute("SELECT * FROM functions WHERE id = %s", (id,))
    func = cur.fetchone()
    name = func['function_name']
    form = EditForm()
    if form.validate_on_submit():
        try:
            # db.session.commit()
            cur.execute("UPDATE functions SET function_name = %s, description = %s, entry_point = %s, modified_at = 'NOW()', function_code = %s WHERE id = %s", (form.name.data, form.desc.data, form.entry_point.data, form.code.data, id))
            conn.commit()
            flash(f'Saved Function "{name}"!', 'success')
            return redirect('../view/' + str(id))
        except:
            flash('There was an issue handling your request.', 'danger')
    form.name.data = func['function_name']
    form.desc.data = func['description']
    form.entry_point.data = func['entry_point']
    # form.language.data = func.language
    form.code.data = func['function_code']
    return render_template('edit.html', title=f'Edit "{form.name.data}"', func=func, form=form, cancel_route="view")


@guiapi.route('/view/<id>')
# @authenticated
def view(id):
    conn, cur = get_db_connection()
    cur.execute("SELECT * FROM functions WHERE id = %s", (id,))
    func = cur.fetchone()
    name = func['function_name']
    return render_template('view.html', title=f'View "{name}"', func=func)


@guiapi.route('/delete/<id>', methods=['POST'])
#@authenticated
def delete(id):
    conn, cur = get_db_connection()
    cur.execute("SELECT id, function_name, deleted FROM functions WHERE id = %s", (id,))
    func = cur.fetchone()
    name = func['function_name']
    if func['deleted'] == False:
        try:
            cur.execute("UPDATE functions SET deleted = True WHERE id = %s", (id,))
            conn.commit()
            flash(f'Deleted Function "{name}".', 'success')
        except:
            flash('There was an issue handling your request.', 'danger')
    else:
        flash('There was an issue handling your request.', 'danger')
    # return redirect(url_for('functions'))
    return redirect(url_for('guiapi.home'))


@guiapi.route('/endpoints')
# @authenticated
def endpoints():

    try:
        conn, cur = get_db_connection()
        cur.execute("SELECT sites.user_id, endpoint_name, endpoint_uuid, status, sites.created_at FROM sites, users WHERE sites.user_id = users.id AND users.username = %s AND endpoint_name is not null order by created_at desc;", (session.get("username"),))
        endpoints = cur.fetchall()

        endpoints_total = len(endpoints)

        cur.execute(
            "select endpoint_uuid from sites, users where user_id = users.id and username = %s and status='ONLINE' and endpoint_uuid is not null",
            (session.get("username"),))
        endpoints_online_all = cur.fetchall()
        endpoints_online = len(endpoints_online_all)

        cur.execute(
            "select endpoint_uuid from sites, users where user_id = users.id and username = %s and status='OFFLINE' and endpoint_uuid is not null",
            (session.get("username"),))
        endpoints_offline_all = cur.fetchall()
        endpoints_offline = len(endpoints_offline_all)

    except:
        flash('There was an issue handling your request', 'danger')
        return redirect(url_for('guiapi.home'))
    return render_template('endpoints.html', title='Endpoints', endpoints=endpoints, endpoints_total=endpoints_total, endpoints_online=endpoints_online, endpoints_offline=endpoints_offline)
