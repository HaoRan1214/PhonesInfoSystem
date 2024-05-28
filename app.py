# 导入所需的模块
from flask import Flask, render_template, request, redirect, url_for, session
import mysql.connector
import json
# 创建 Flask 应用实例
app = Flask(__name__)
# 配置 MySQL 数据库连接信息
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = '123456'
app.config['MYSQL_DB'] = 'python'
# 设置应用的密钥
app.secret_key = 'secret_key'
# 连接 MySQL 数据库
mysql = mysql.connector.connect(
    host=app.config['MYSQL_HOST'],
    user=app.config['MYSQL_USER'],
    password=app.config['MYSQL_PASSWORD'],
    database=app.config['MYSQL_DB']
)

# 定义 Phone 类，表示手机对象
class Phone():
    def __init__(self, id, brand, model, price, votes):
        self.id = id
        self.brand = brand
        self.model = model
        self.price = price
        self.votes = votes

    def __repr__(self):
        return f'<Phone {self.id}>'

    def __json__(self):
        return {'id': self.id, 'brand': self.brand, 'model': self.model, 'price': self.price, 'votes': self.votes}

# 定义 User 类，表示用户对象
class User():
    def __init__(self, id, username, password):
        self.id = id
        self.username = username
        self.password = password

    def __repr__(self):
        return f'<User {self.username}>'

# 路由：重定向到登录页面
@app.route('/')
def toLogin():
    return redirect(url_for('login'))

# 路由：显示主页
@app.route('/index')
def index():
    # 获取数据库游标
    cur = mysql.cursor()
    # 执行查询语句获取所有手机数据
    cur.execute("SELECT * FROM phones")
    # 将查询结果封装为 Phone 对象列表
    phones = []
    for id, brand, model, price, votes in cur.fetchall():
        phones.append(Phone(id=id, brand=brand, model=model, price=price, votes=votes))
    cur.close()
    # 渲染主页模板并传递手机数据
    return render_template('index.html', phones=phones)

# 路由：显示 echarts 页面
@app.route('/echarts')
def echarts():
    cur = mysql.cursor()
    cur.execute("SELECT * FROM phones")
    phones = []
    for row in cur.fetchall():
        phones.append(Phone(id=row[0], brand=row[1], model=row[2], price=row[3], votes=row[4]))  # 添加 votes 参数
    cur.close()
    phones = json.dumps([phone.__json__() for phone in phones])
    return render_template('echarts.html', phones=phones)


# 路由：添加手机信息
@app.route('/add', methods=['GET', 'POST'])
def add():
    if request.method == 'POST':
        brand = request.form['brand']
        model = request.form['model']
        price = request.form['price']
        cur = mysql.cursor()
        cur.execute("INSERT INTO phones (brand, model, price) VALUES (%s,%s, %s)", (brand, model, price))
        mysql.commit()
        cur.close()
        return redirect(url_for('index'))
    return render_template('add.html')

# 路由：编辑手机信息
@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit(id):
    cur = mysql.cursor()
    cur.execute("SELECT * FROM phones WHERE id = %s", (id,))
    phone = cur.fetchone()
    if request.method == 'POST':
        brand = request.form['brand']
        model = request.form['model']
        price = request.form['price']
        cur.execute("UPDATE phones SET brand = %s, model = %s, price = %s WHERE id = %s", (brand, model, price, id))
        mysql.commit()
        cur.close()
        return redirect(url_for('index'))
    cur.close()
    return render_template('edit.html', phone=phone)

# 路由：删除手机信息
@app.route('/delete/<int:id>')
def delete(id):
    cur = mysql.cursor()
    cur.execute("DELETE FROM phones WHERE id = %s", (id,))
    mysql.commit()
    cur.close()
    return redirect(url_for('index'))

# 路由：用户登录
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        cur = mysql.cursor()
        cur.execute("SELECT * FROM users WHERE username = %s", (username,))
        user = cur.fetchone()
        if user is None:
            error = 'Invalid Credentials. Please try again.'
            return render_template('login.html', error=error)
        else:
            if user:
                session['username'] = user[1]
                return redirect(url_for('index'))
            else:
                error = 'Invalid Credentials. Please try again.'
                return render_template('login.html', error=error)
        cur.close()
    return render_template('login.html')

# 路由：用户注册
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        cur = mysql.cursor()
        cur.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, password))
        mysql.commit()
        cur.close()
        return redirect(url_for('login'))
    return render_template('register.html')

# 路由：用户注销
@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

# 路由：处理投票
@app.route('/vote', methods=['GET', 'POST'])
def vote():
    if request.method == 'POST':
        phone_id = request.form.get('phone_id')
        if phone_id is not None:
            cur = mysql.cursor()
            cur.execute("UPDATE phones SET votes = votes + 1 WHERE id = %s", (phone_id,))
            mysql.commit()
            cur.close()
            # 重定向到相同页面以刷新投票数
            return redirect(url_for('vote'))
        else:
            # 处理未提供 phone_id 的情况
            return "Phone ID not provided"
    else:
        # 渲染投票页面前获取手机数据
        cur = mysql.cursor()
        cur.execute("SELECT * FROM phones")
        phones = []
        for id, brand, model, price, votes in cur.fetchall():
            phones.append(Phone(id=id, brand=brand, model=model, price=price, votes=votes))
        cur.close()
        # 渲染投票页面并传递手机数据
        return render_template('vote.html', phones=phones)

#应用入口
if __name__ == '__main__':
    app.run(debug=True)
