from flask import Flask ,redirect , render_template,session,flash,url_for,request
import docker
from docker.errors import APIError
from flask_login import LoginManager, UserMixin, login_required, login_user, logout_user, current_user
import mysql.connector
from jinja2 import Template
import re
import bcrypt


app = Flask(__name__)
app.secret_key = 'you_wont_understand_shit_here'
client = docker.from_env()

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return users.get(user_id)
# User class
class User(UserMixin):
    def __init__(self, id):
        self.id = id

# In-memory user store for demonstration purposes
users = {'1': User('1')}

# User loader function
@login_manager.user_loader
def load_user(user_id):
    return users.get(user_id)


# MySQL configuration
db_config = {
    'user': 'root',
    'password': 'Ash@2003',
    'host': 'localhost',
    'port': '3306',
    'database': 'user_system'
}

# Function to create the table
def create_tables():
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS user (
        id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(100) NOT NULL,
        email VARCHAR(100) NOT NULL UNIQUE,
        password VARCHAR(100) NOT NULL
    );
    """)
    conn.commit()
    conn.close()

# Call create_tables function to ensure the table is created
create_tables()

# Function to establish database connection
def get_db_connection():
    conn = mysql.connector.connect(**db_config)
    return conn

# Function to validate password strength
def validate_password(password):
    # Password must contain at least one uppercase, one lowercase, and one special character
    return any(char.isupper() for char in password) \
        and any(char.islower() for char in password) \
        and any(not char.isalnum() for char in password)

# Routes
@app.route('/')
@app.route('/login', methods=['GET', 'POST'])
def login():
    message = ''
    if request.method == 'POST' and 'email' in request.form and 'password' in request.form:
        email = request.form['email']
        password = request.form['password'].encode('utf-8')
        
        # Query the User model
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM user WHERE email=%s", (email,))
        user = cursor.fetchone()
        conn.close()
        
        if user and bcrypt.checkpw(password, user['password'].encode('utf-8')):
            session['email'] = email
            flash('Logged in successfully')
            session['loggedin'] = True
            session['userid'] = user['id']
            session['name'] = user['name']
            session['email'] = user['email']
            flash('Logged in successfully!')
            return redirect("/home")
        else:
            flash('Please enter correct email / password!')
    
    return render_template('login.html', message=message,logged_in='loggedin' in session)
@app.route('/logout')
def logout():
    session.pop('loggedin', None)
    session.pop('userid', None)
    session.pop('email', None)
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    create_tables()
    message = ''
    if request.method == 'POST' and 'name' in request.form and 'password' in request.form and 'email' in request.form and 'confirm_password' in request.form:
        userName = request.form['name']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        if password != confirm_password:
            return 'Passwords do not match'

        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        # Check if email already exists
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM user WHERE email=%s", (email,))
        existing_user = cursor.fetchone()
        
        if existing_user:
            message = 'Account already exists!'
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            message = 'Invalid email address!'
        elif not userName or not password or not email:
            message = 'Please fill out the form!'
        elif password != confirm_password:
            message = 'Passwords do not match!'
        elif not validate_password(password):
            message = 'Password must contain at least one uppercase letter, one lowercase letter, and one special character.'
        else:
            # Create new user
            cursor.execute("INSERT INTO user (name, email, password) VALUES (%s, %s, %s)",
                        (userName, email, hashed_password))
            conn.commit()
            conn.close()
            flash('You have successfully registered!')
            return redirect("/login")
    elif request.method == 'POST':
        flash('Please fill out the form!')
    
    return render_template('register.html', message=message, logged_in='loggedin' in session)



#Home page
@app.route('/home')
def home():
    return render_template('home.html',logged_in='loggedin')

#image pulling and conatiner building
def create(image_name_or_id, container_name):
    messages = {'success':[], 'error':[]}
    
    try:
        # Check if image_name_or_id is an image ID or name
        if len(image_name_or_id) == 64 and all(c in "abcdef0123456789" for c in image_name_or_id.lower()):
            # Assuming image_name_or_id is an image ID (image IDs are 64 characters hexadecimal)
            image = client.images.get(image_name_or_id)
            messages['success'].append(f'Found Docker image by ID: {image_name_or_id}')
        else:
            # Assuming image_name_or_id is an image name
            image = client.images.pull(image_name_or_id)
            messages['success'].append(f'Successfully pulled Docker image: {image_name_or_id}')
        
        messages['success'].append(f'Image ID: {image.id}')
        print(f'Image name : {image_name_or_id}')
        print(f'Image ID : {image.id}')
        
        # Create and start container
        container = client.containers.run(image.id, detach=True, name=container_name)
        messages['success'].append(f'Successfully created Docker container for image {image_name_or_id}')
        messages['success'].append(f'Container name: {container.name}')
        messages['success'].append(f'Container ID: {container.id}')
        
        # Start the container (if not already started)
        con = client.containers.get(container.id)
        con.start()
        
    except Exception as e:
        messages['error'].append(f"Error: Failed to create or start container '{container_name}' - {e}")
    
    return messages
    
def Image(image_name):
    messages = {'success':[], 'error':[]}
    try:
        image = client.images.pull(image_name)
        messages['success'].append(f'Successfully pulled docker image: {image_name}')
        messages['success'].append(f'Image ID:{image.id}')
        print(f'Image name : {image_name}')
        print(f'Image ID : {image.id}')
    except Exception as e:
        messages['error'].append(f"Error: Image not pulled - {e}")
    return messages

#Pulling image and creating containers
@app.route('/Pullimage', methods=['GET','POST'])
def pullImage():
    message=''
    messages = {'success':[], 'error':[]}
    if request.method == 'POST':
        image_name = request.form['image_name']
        messages = Image(image_name)
        message = "Image has been pulled" if not messages['error'] else "Image pull failed"
    
    return render_template('pullImage.html',message=message, messages=messages,logged_in='loggedin')



@app.route('/CreateContainer', methods=['GET','POST'])
def CreateContainer():
    message = ""
    messages = {'sucess':[], 'error':[]}
    if request.method == 'POST':
        image_name = request.form['image_name']
        container_name = request.form['container_name']
        messages=create(image_name,container_name)
        message = "Container has been created" if not messages['error'] else "Container creation failed"
    return render_template('CreateContainer.html', message=message, messages=messages,logged_in='loggedin')


def format_size(size):
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024:
            return f"{size:.2f} {unit}"
        size /= 1024
    return f"{size:.2f} PB"

@app.route('/listImages')
def list_images():
    try:
        images = client.images.list()
        image_data = []
        for image in images:
            has_container = False
            for con in client.containers.list(all=True):
                if con.image.id == image.id:
                    has_container = True
                    break
            
            # Handle cases where RepoTags might be missing or empty
            repo_tags = image.attrs['RepoTags'][0] if image.attrs.get('RepoTags') else '<none>:<none>'
            # Split the repo_tags into image_name and image_tag
            image_name, image_tag = repo_tags.split(':') if ':' in repo_tags else (repo_tags, '<none>')
            # Format the image size
            formatted_size = format_size(image.attrs['Size'])
            image_info = {
                'image_name': image_name,
                'image_tag': image_tag,
                'image_id': image.id,
                'size': formatted_size,
                'has_container': has_container
            }
            image_data.append(image_info)
        
    except Exception as e:
        print(f"Error: {e}")
        image_data = []

    return render_template('list_images.html', images=image_data,logged_in='loggedin')



@app.route('/listContainers')
def list_containers():
    try:
        containers = client.containers.list(all=True)
    except Exception as e:
        print(f"Error: {e}") 
    return render_template('list_containers.html',containers = containers,logged_in='loggedin')

#Removing and Stoping
@app.route('/RemoveContainer')
def RemoveContainer():
    container_id = request.args.get('container_id')
    container_name = request.args.get('container_name')
    message = f"Container {container_name} with ID {container_id} has been removed."
    client.containers.get(container_id).stop()
    client.containers.get(container_id).remove()
    flash(message)

    return redirect('/listContainers')

@app.route('/StopContainer')
def StopContainer():
    container_id = request.args.get('container_id')
    container_name = request.args.get('container_name')
    message = f"Container {container_name} with ID {container_id} has been stopped."
    client.containers.get(container_id).stop()
    flash(message)
    return redirect('/listContainers')

@app.route('/removeImage')
def remove_image():
    image_id = request.args.get('image_id')
    try:
        # Check if there are dependent containers
        dependent_container = False
        for con in client.containers.list(all=True):
            if con.image.id == image_id:
                dependent_container = True
                break
        
        if dependent_container:
            return redirect('/listImages?message=Cannot delete image as there is a dependent container&id=2')

        # Check if id is 2, prevent deletion with a message
        id = int(request.args.get('id', 0))
        if id == 2:
            return redirect('/listImages?message=Deletion not allowed&id=2')
        
        # Proceed with image deletion
        client.images.remove(image_id)
        return redirect('/listImages')
    
    except APIError as e:
        return redirect('/listImages?message=Error occurred while deleting image')
#Dockerfile
@app.route('/CreateDockerfile', methods=['POST','GET'])
def createDockerfile():
    dockerfile_content = ''
    if request.method == 'POST':
        base_image = request.form['base_image']
        packages = request.form['packages']
        exposed_port = request.form['exposed_port']
        cmd = request.form['cmd']

            
        
        template = Template("""
            #Use an appropriate base image
            FROM {{base_image}}
                            
            #Install pacakges
            RUN apt-get update && apt-get install -y \\
                {{packages}}\\
                && rm -rf /var/lib/apt/lists/*
            
            #Set working directory
            WORKDIR /app
                            
            #Copy application files into the container
            COPY . .
            
            #Expose port
            EXPOSE {{ exposed_port }}
            
            #Define the startuo commnand
            CMD {{cmd}}                         
        """)

        dockerfile_content = template.render(
            base_image=base_image,
            packages=packages,
            exposed_port = exposed_port,
            cmd=cmd
        )

        output_file = 'Dockerfile'
        with open(output_file , 'w')as f:
            f.write(dockerfile_content)
        
    return render_template('CreateDockerfile.html', dockerfile=dockerfile_content,logged_in='loggedin')



if __name__ == '__main__':
    app.run(debug=True)