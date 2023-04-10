from string import digits, ascii_letters

# static files
STATIC_IMAGES_URL = '/images'

# database
DB_NAME = 'dev'

# email
EMAIL_FROM = 'PyRobots'
EMAIL_USER = 'pyrobot.defaultname@gmail.com'
EMAIL_VALIDATION_SUBJECT = 'Account validation code'
EMAIL_RECOVER_SUBJECT = 'Password recover code'
EMAIL_PASSWORD = 'nprwdumhheyhcqnl'
EMAIL_SERVER = 'smtp.gmail.com'
EMAIL_PORT = 465

# user validation
VALIDATION_CODE_LENGTH = 4

# password recover
RECOVER_CODE_LENGTH = 4
RECOVER_CODE_ELEMS = digits + ascii_letters

# frontend
FRONTEND_URL = 'http://localhost:3000'

# directories
ROBOTS_DIR = 'robots'
IMAGES_DIR = 'images'

# authentication
SECRET_KEY = "187f845bcdd978968a31f876b5fe1508438eeffb36c4868ce6c727eeb0d6354e"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# avatar
AVATAR_STRING_ENCODE = 'utf-8'

# game
GAME_ROUNDS = 100
SCANNER_DISTANCE = 1500
DISTANCE_MISSILE_ROUND = 10
COOLDOWN_MISSILE = 3
DAMAGE_COLLISION = 2
DAMAGE_MISSIL_MIN = 3
DAMAGE_MISSIL_MED = 5
DAMAGE_MISSIL_MAX = 10
MAX_ACCEL_TO_TURN = 50

# robot movement
VAR_ACCEL = 2
MAX_ACCEL = 100

# default robots info
DEFAULT_ROBOTS = {
    'Default1':
        'from robot import Robot\n'
        '\n\n'
        'class Default1(Robot):\n'
        '    def initialize(self):\n'
        '        self.i = 0\n'
        '        self.delta_vel = 100 - self.get_damage()\n'
        '        self.reverse = False\n'
        '        self.last_position = self.get_position()\n'
        '        self.last_velocity = self.get_velocity()\n'
        '    def respond(self):\n'
        '        if self.i % 10 == 0:\n'
        '            self.drive(self.get_direction() + 45,'
        'self.get_velocity() + self.delta_vel)\n'
        '        self.i += 1\n'
        '        if self.last_position == self.get_position():\n'
        '            self.reverse = not self.reverse\n'
        '            self.drive(self.get_direction() + 180, 35)\n'
        '        if self.last_velocity > 75:\n'
        '            self.delta_vel = -5\n'
        '        elif self.last_velocity < 15:\n'
        '            self.delta_vel = 5\n',
    'Default2':
        'from robot import Robot\n'
        '\n\n'
        'class Default2(Robot):\n'
        '    def initialize(self):\n'
        '        self.last_direction = 0\n'
        '    def respond(self):\n'
        '        if self.scanned() != -1:\n'
        '            self.cannon(self.last_direction, self.scanned())\n'
        '        self.last_direction += 10\n'
        '        self.point_scanner(self.last_direction, 10)\n'
}
