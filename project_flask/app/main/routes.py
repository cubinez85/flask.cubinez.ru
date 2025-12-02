from datetime import datetime, timezone
from flask import render_template, flash, redirect, url_for, request, g, \
    current_app, jsonify, send_file, abort
from flask_login import current_user, login_required
from flask_babel import _, get_locale
import sqlalchemy as sa
import re
import os
import uuid
from werkzeug.utils import secure_filename
from app import db
from app.main.forms import EditProfileForm, EmptyForm, PostForm, SearchForm, MessageForm
from app.models import User, Post, Message, Notification, Employee, Follow
from app.main import bp
from app import push
from sqlalchemy.sql import text

@bp.before_app_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.now(timezone.utc)
        db.session.commit()
        g.search_form = SearchForm()
    g.locale = str(get_locale())

def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif', 'pdf', 'doc', 'docx', 'txt', 'zip',
                         'mp4', 'mp3', 'avi', 'mov', 'wav', 'rar', '7z',
                         'xls', 'xlsx', 'xlsm', 'xlsb'}
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def notify_mention(user, post):
    """Уведомление об упоминании в посте"""
    user.add_notification('mention', {
        'post_id': post.id,
        'author': post.author.username,
        'excerpt': post.body[:50] + '...' if len(post.body) > 50 else post.body
    })
    db.session.commit()

def notify_new_post(follower, author, post):
    """Уведомление о новом посте от подписанного автора"""
    follower.add_notification('new_post', {
        'post_id': post.id,
        'author': author.username,
        'excerpt': post.body[:50] + '...' if len(post.body) > 50 else post.body
    })
    db.session.commit()

def notify_new_follower(user, follower):
    """Уведомление о новом подписчике"""
    user.add_notification('new_follower', {
        'follower_id': follower.id,
        'follower_username': follower.username
    })
    db.session.commit()

@bp.route('/', methods=['GET', 'POST'])
@bp.route('/index', methods=['GET', 'POST'])
@login_required
def index():
    form = PostForm()
    if form.validate_on_submit():
        current_app.logger.info("=== DEBUG: Form validation PASSED ===")
        current_app.logger.info(f"Post content: {form.post.data}")
        current_app.logger.info(f"File attached: {form.attachment.data is not None}")

        # Обработка файла
        filename = None
        file_path = None
        file_size = None
        file_mimetype = None
        unique_filename = None  # Добавлено для исправления ошибки

        if form.attachment.data:
            file = form.attachment.data
            current_app.logger.info(f"File name: {file.filename}")

            # Временно читаем размер файла для отладки
            file_data = file.read()
            file_size_debug = len(file_data)
            file.seek(0)  # Reset file pointer after reading
            current_app.logger.info(f"File size (debug): {file_size_debug} bytes")

            if file and allowed_file(file.filename):
                current_app.logger.info("File type is allowed")
                # Создаем уникальное имя файла
                filename = secure_filename(file.filename)
                unique_filename = str(uuid.uuid4()) + '_' + filename

                # Создаем папку для загрузок если её нет
                upload_folder = os.path.join(current_app.root_path, 'static', 'uploads')
                current_app.logger.info(f"Upload folder: {upload_folder}")
                current_app.logger.info(f"Unique filename: {unique_filename}")

                os.makedirs(upload_folder, exist_ok=True)

                file_path = os.path.join(upload_folder, unique_filename)
                current_app.logger.info(f"Full file path: {file_path}")

                try:
                    file.save(file_path)
                    file_size = os.path.getsize(file_path)
                    file_mimetype = file.content_type
                    current_app.logger.info(f"File saved successfully: {file_path}")
                    current_app.logger.info(f"File size: {file_size} bytes")
                    current_app.logger.info(f"MIME type: {file_mimetype}")
                except Exception as e:
                    current_app.logger.error(f"Error saving file: {e}")
                    flash(_('Error saving file: %(error)s', error=str(e)))
            else:
                current_app.logger.warning("File type not allowed or no file")
                if file:
                    flash(_('File type not allowed: %(filename)s', filename=file.filename))
        else:
            current_app.logger.info("No file attached to the post")

        # Создание поста - ИСПРАВЛЕНИЕ: используем unique_filename вместо filename
        post = Post(
            body=form.post.data,
            author=current_user,
            filename=unique_filename,  # Исправлено: используем UUID имя
            file_path=file_path,
            file_size=file_size,
            file_mimetype=file_mimetype
        )
        db.session.add(post)
        db.session.commit()
        current_app.logger.info(f"Post created with ID: {post.id}, Has file: {post.has_file()}")
        current_app.logger.info(f"Post filename in DB: {post.filename}")

        # Проверяем упоминания и отправляем уведомления
        mentions = re.findall(r'@(\w+)', form.post.data)
        for username in mentions:
            mentioned_user = db.session.scalar(
                sa.select(User).where(User.username == username))
            if mentioned_user and mentioned_user != current_user:
                notify_mention(mentioned_user, post)

        # ИСПРАВЛЕНИЕ: Правильная работа с WriteOnly коллекцией followers
        # Получаем подписчиков через запрос
        followers_query = sa.select(Follow.follower_id).where(Follow.followed_id == current_user.id)
        follower_ids = [row[0] for row in db.session.execute(followers_query).all()]

        # Уведомляем подписчиков о новом посте
        for follower_id in follower_ids:
            if follower_id != current_user.id:  # Не уведомляем себя
                follower = db.session.get(User, follower_id)
                if follower:
                    notify_new_post(follower, current_user, post)

        flash(_('Your post is now live!'))
        return redirect(url_for('main.index'))
    elif request.method == 'POST':
        current_app.logger.error("=== DEBUG: Form validation FAILED ===")
        current_app.logger.error(f"Form errors: {form.errors}")
        for field, errors in form.errors.items():
            for error in errors:
                current_app.logger.error(f"Field '{field}': {error}")
                flash(f"Error in {field}: {error}", 'error')

    page = request.args.get('page', 1, type=int)
    posts = db.paginate(current_user.following_posts(), page=page,
                        per_page=current_app.config['POSTS_PER_PAGE'],
                        error_out=False)
    next_url = url_for('main.index', page=posts.next_num) \
        if posts.has_next else None
    prev_url = url_for('main.index', page=posts.prev_num) \
        if posts.has_prev else None
    return render_template('index.html', title=_('Home'), form=form,
                           posts=posts.items, next_url=next_url,
                           prev_url=prev_url)


@bp.route('/explore')
@login_required
def explore():
    page = request.args.get('page', 1, type=int)
    query = sa.select(Post).order_by(Post.timestamp.desc())
    posts = db.paginate(query, page=page,
                        per_page=current_app.config['POSTS_PER_PAGE'],
                        error_out=False)
    next_url = url_for('main.explore', page=posts.next_num) \
        if posts.has_next else None
    prev_url = url_for('main.explore', page=posts.prev_num) \
        if posts.has_prev else None
    return render_template('index.html', title=_('Explore'),
                           posts=posts.items, next_url=next_url,
                           prev_url=prev_url)


@bp.route('/user/<username>')
@login_required
def user(username):
    user = db.first_or_404(sa.select(User).where(User.username == username))
    page = request.args.get('page', 1, type=int)
    query = user.posts.select().order_by(Post.timestamp.desc())
    posts = db.paginate(query, page=page,
                        per_page=current_app.config['POSTS_PER_PAGE'],
                        error_out=False)
    next_url = url_for('main.user', username=user.username,
                       page=posts.next_num) if posts.has_next else None
    prev_url = url_for('main.user', username=user.username,
                       page=posts.prev_num) if posts.has_prev else None
    form = EmptyForm()
    return render_template('user.html', user=user, posts=posts.items,
                           next_url=next_url, prev_url=prev_url, form=form)

@bp.route('/user/<username>/popup')
@login_required
def user_popup(username):
    user = db.first_or_404(sa.select(User).where(User.username == username))
    form = EmptyForm()
    return render_template('user_popup.html', user=user, form=form)


@bp.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm(current_user.username)
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.about_me = form.about_me.data
        db.session.commit()
        flash(_('Your changes have been saved.'))
        return redirect(url_for('main.edit_profile'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.about_me.data = current_user.about_me
    return render_template('edit_profile.html', title=_('Edit Profile'),
                           form=form)


@bp.route('/follow/<username>', methods=['POST'])
@login_required
def follow(username):
    form = EmptyForm()
    if form.validate_on_submit():
        user = db.session.scalar(
            sa.select(User).where(User.username == username))
        if user is None:
            flash(_('User %(username)s not found.', username=username))
            return redirect(url_for('main.index'))
        if user == current_user:
            flash(_('You cannot follow yourself!'))
            return redirect(url_for('main.user', username=username))
        current_user.follow(user)
        db.session.commit()

        # Отправляем уведомление о новом подписчике
        notify_new_follower(user, current_user)

        flash(_('You are following %(username)s!', username=username))
        return redirect(url_for('main.user', username=username))
    else:
        return redirect(url_for('main.index'))


@bp.route('/unfollow/<username>', methods=['POST'])
@login_required
def unfollow(username):
    form = EmptyForm()
    if form.validate_on_submit():
        user = db.session.scalar(
            sa.select(User).where(User.username == username))
        if user is None:
            flash(_('User %(username)s not found.', username=username))
            return redirect(url_for('main.index'))
        if user == current_user:
            flash(_('You cannot unfollow yourself!'))
            return redirect(url_for('main.user', username=username))
        current_user.unfollow(user)
        db.session.commit()
        flash(_('You are not following %(username)s.', username=username))
        return redirect(url_for('main.user', username=username))
    else:
        return redirect(url_for('main.index'))


def build_tree(parent_id=None):
    """Рекурсивная функция для построения дерева сотрудников"""
    employees = Employee.query.filter_by(parent=parent_id).all()
    tree = []
    for employee in employees:
        tree.append({
            'employee': employee,
            'children': build_tree(employee.id)
        })
    return tree

@bp.route('/employees')
@login_required
def employees():
    """Страница со списком всех сотрудников"""
    employees = Employee.query.all()
    return render_template('employees.html', employees=employees)

@bp.route('/hierarchy')
@login_required
def hierarchy():
    """Страница с иерархией сотрудников в виде дерева"""
    tree_data = build_tree()
    return render_template('hierarchy.html', tree=tree_data)

@bp.route('/orgchart')
@login_required
def orgchart():
    """Страница с интерактивной организационной диаграммой"""
    employees = Employee.query.all()
    return render_template('orgchart.html', employees=employees)

@bp.route('/blog')
def blog():
    cursor = db.session.execute(
        text('select user.id, user.username, user.about_me, user.last_seen, post.body,\n'
             'post.timestamp from user, post where user.id = post.user_id')
    )
    content = cursor.fetchall()
    cursor = db.session.execute(
        text('select user.id, user.username, user.about_me, user.last_seen, post.body,\n'
             'post.timestamp from user, post where user.id = post.user_id')
    )
    labels = cursor.fetchall()
    labels = list(map(lambda x: x[0:], cursor.keys()))

    return render_template('blog.html', labels=labels, content=content)

@bp.route('/followers')
def followers():
    cursor = db.session.execute(text('select user.id, user.username, followers.follower_id,\n'
                                     'followers.followed_id from user, followers where user.id = followers.follower_id'))
    content = cursor.fetchall()
    cursor = db.session.execute(text('select user.id, user.username, followers.follower_id,\n'
                                     'followers.followed_id from user, followers where user.id = followers.follower_id'))
    labels = cursor.fetchall()
    labels = list(map(lambda x: x[0:], cursor.keys()))

    return render_template('followers.html', labels=labels, content=content)

@bp.route('/search')
@login_required
def search():
    if not g.search_form.validate():
        return redirect(url_for('main.explore'))
    page = request.args.get('page', 1, type=int)
    posts, total = Post.search(g.search_form.q.data, page,
                               current_app.config['POSTS_PER_PAGE'])
    next_url = url_for('main.search', q=g.search_form.q.data, page=page + 1) \
        if total > page * current_app.config['POSTS_PER_PAGE'] else None
    prev_url = url_for('main.search', q=g.search_form.q.data, page=page - 1) \
        if page > 1 else None
    return render_template('search.html', title=_('Search'), posts=posts,
                           next_url=next_url, prev_url=prev_url)

@bp.route('/send_message/<recipient>', methods=['GET', 'POST'])
@login_required
def send_message(recipient):
    user = db.first_or_404(sa.select(User).where(User.username == recipient))
    form = MessageForm()
    if form.validate_on_submit():
        current_app.logger.info("=== DEBUG MESSAGE: Form validation PASSED ===")
        current_app.logger.info(f"Message content: {form.message.data}")
        current_app.logger.info(f"File attached: {form.attachment.data is not None}")

        # Обработка файла
        filename = None
        file_path = None
        file_size = None
        file_mimetype = None
        unique_filename = None  # Добавлено для исправления ошибки

        if form.attachment.data:
            file = form.attachment.data
            current_app.logger.info(f"File name: {file.filename}")

            # Временно читаем размер файла для отладки
            file_data = file.read()
            file_size_debug = len(file_data)
            file.seek(0)  # Reset file pointer after reading
            current_app.logger.info(f"File size (debug): {file_size_debug} bytes")

            if file and allowed_file(file.filename):
                current_app.logger.info("File type is allowed")
                # Создаем уникальное имя файла
                filename = secure_filename(file.filename)
                unique_filename = str(uuid.uuid4()) + '_' + filename

                # Создаем папку для загрузок если её нет
                upload_folder = os.path.join(current_app.root_path, 'static', 'uploads')
                current_app.logger.info(f"Upload folder: {upload_folder}")
                current_app.logger.info(f"Unique filename: {unique_filename}")

                os.makedirs(upload_folder, exist_ok=True)

                file_path = os.path.join(upload_folder, unique_filename)
                current_app.logger.info(f"Full file path: {file_path}")

                try:
                    file.save(file_path)
                    file_size = os.path.getsize(file_path)
                    file_mimetype = file.content_type
                    current_app.logger.info(f"File saved successfully: {file_path}")
                    current_app.logger.info(f"File size: {file_size} bytes")
                    current_app.logger.info(f"MIME type: {file_mimetype}")
                except Exception as e:
                    current_app.logger.error(f"Error saving file: {e}")
                    flash(_('Error saving file: %(error)s', error=str(e)))
            else:
                current_app.logger.warning("File type not allowed or no file")
                if file:
                    flash(_('File type not allowed: %(filename)s', filename=file.filename))
        else:
            current_app.logger.info("No file attached to the message")

        # Создание сообщения - ИСПРАВЛЕНИЕ: используем unique_filename вместо filename
        msg = Message(
            author=current_user,
            recipient=user,
            body=form.message.data,
            filename=unique_filename,  # Исправлено: используем UUID имя
            file_path=file_path,
            file_size=file_size,
            file_mimetype=file_mimetype
        )
        db.session.add(msg)
        user.add_notification('unread_message_count',
                              user.unread_message_count())
        db.session.commit()
        current_app.logger.info(f"Message created with ID: {msg.id}, Has file: {msg.has_file()}")
        current_app.logger.info(f"Message filename in DB: {msg.filename}")

        # Отправляем push-уведомление о новом сообщении
        push.notify_new_message(user, current_user, msg)

        flash(_('Your message has been sent.'))
        return redirect(url_for('main.user', username=recipient))
    elif request.method == 'POST':
        current_app.logger.error("=== DEBUG MESSAGE: Form validation FAILED ===")
        current_app.logger.error(f"Form errors: {form.errors}")
        for field, errors in form.errors.items():
            for error in errors:
                current_app.logger.error(f"Field '{field}': {error}")
                flash(f"Error in {field}: {error}", 'error')

    return render_template('send_message.html', title=_('Send Message'),
                           form=form, recipient=recipient)

@bp.route('/messages')
@login_required
def messages():
    current_user.last_message_read_time = datetime.now(timezone.utc)
    current_user.add_notification('unread_message_count', 0)
    db.session.commit()
    page = request.args.get('page', 1, type=int)
    query = current_user.messages_received.select().order_by(
        Message.timestamp.desc())
    messages = db.paginate(query, page=page,
                           per_page=current_app.config['POSTS_PER_PAGE'],
                           error_out=False)
    next_url = url_for('main.messages', page=messages.next_num) \
        if messages.has_next else None
    prev_url = url_for('main.messages', page=messages.prev_num) \
        if messages.has_prev else None
    return render_template('messages.html', messages=messages.items,
                           next_url=next_url, prev_url=prev_url)

@bp.route('/download/<int:message_id>')
@login_required
def download_file(message_id):
    message = Message.query.get_or_404(message_id)

    # Проверка прав доступа
    if message.author != current_user and message.recipient != current_user:
        flash(_('You do not have permission to access this file.'))
        return redirect(url_for('main.index'))

    if not message.file_path or not os.path.exists(message.file_path):
        flash(_('File not found.'))
        return redirect(url_for('main.index'))

    return send_file(message.file_path,
                     as_attachment=True,
                     download_name=message.filename)

@bp.route('/download_post/<int:post_id>')
@login_required
def download_post_file(post_id):
    post = db.session.get(Post, post_id)
    if not post or not post.filename:
        current_app.logger.error(f"Post {post_id} not found or has no filename")
        abort(404)

    upload_folder = current_app.config['UPLOAD_FOLDER']
    file_path = os.path.join(upload_folder, post.filename)
    
    if not os.path.exists(file_path):
        current_app.logger.error(f"File not found at: {file_path}")
        abort(404)
    
    # Определяем оригинальное имя
    if '_' in post.filename and len(post.filename.split('_')[0]) == 36:
        original_name = post.filename.split('_', 1)[1]
    else:
        original_name = post.filename
    
    # Определяем действие: скачивание или просмотр
    action = request.args.get('action', 'download')
    
    current_app.logger.info(f"File request - Post: {post_id}, Action: {action}, File: {original_name}")
    
    if action == 'view' and post.file_mimetype and post.file_mimetype.startswith('image/'):
        # Для просмотра изображений в браузере
        return send_file(file_path, as_attachment=False)
    else:
        # Для скачивания (по умолчанию)
        return send_file(
            file_path,
            as_attachment=True,
            download_name=original_name,
            mimetype=post.file_mimetype
        )

@bp.route('/debug_upload', methods=['GET', 'POST'])
@login_required
def debug_upload():
    if request.method == 'POST':
        current_app.logger.info("=== DEBUG UPLOAD ENDPOINT ===")
        current_app.logger.info(f"Request method: {request.method}")
        current_app.logger.info(f"Request form: {dict(request.form)}")
        current_app.logger.info(f"Request files: {list(request.files.keys())}")

        if 'attachment' in request.files:
            file = request.files['attachment']
            current_app.logger.info(f"File object: {file}")
            current_app.logger.info(f"File filename: {file.filename}")
            current_app.logger.info(f"File content_type: {file.content_type}")

            if file and file.filename != '':
                # Простая загрузка без валидации
                filename = secure_filename(file.filename)
                upload_folder = os.path.join(current_app.root_path, 'static', 'uploads')
                file_path = os.path.join(upload_folder, f"debug_{filename}")

                try:
                    file.save(file_path)
                    current_app.logger.info(f"DEBUG: File saved to {file_path}")
                    return f"SUCCESS: File '{filename}' uploaded via debug endpoint"
                except Exception as e:
                    current_app.logger.error(f"DEBUG: Error: {e}")
                    return f"ERROR: {e}"
            else:
                return "No file selected"
        else:
            return "No file field in request"

    return '''
    <h1>Debug File Upload</h1>
    <form method="post" enctype="multipart/form-data">
        <input type="file" name="attachment"><br>
        <input type="submit" value="Upload Test">
    </form>
    '''

@bp.route('/notifications')
@login_required
def notifications():
    since = request.args.get('since', 0.0, type=float)
    query = current_user.notifications.select().where(
        Notification.timestamp > since).order_by(Notification.timestamp.asc())
    notifications = db.session.scalars(query)
    return [{
        'name': n.name,
        'data': n.get_data(),
        'timestamp': n.timestamp
    } for n in notifications]
