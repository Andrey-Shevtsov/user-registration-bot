import psycopg as pg
from telethon import TelegramClient, events, Button
from telethon.events import StopPropagation


api_id = 1558143    # telegram API id
api_hash = '74626f35b294a17016d6a843df5c3c18'   # telegram API hash

active_dialogs = {}     # dictionary for tracking on which step user is
users = {}     # nested dictionary for users that are going to be added in DB
companies = {}  # nested dictionary for companies that are going to be added


def connectToDB():      # method that establishes connection between bot and DB
    try:
        db = pg.connect("dbname=BotTestDB user=postgres password=2516282752")   # passing DB name, username and password needed for connection to the DB
        print("successfully connected to DB")
        return db
    except:     # if connection attempt failed - print error message
        print("an error occurred")
        return None


def stateEquals(user_id, state):    # method that checks if user being on specified state
    return bool(active_dialogs[str(user_id)] == state)


with TelegramClient('test', api_id, api_hash) as client:    # start of the bot
    database = connectToDB()
    cursor = database.cursor()

    @client.on(events.NewMessage(pattern=r'(?i).*/start'))      # method that handling /start command (not final)
    async def startHandler(event):
        global role
        global workplace
        global user_name
        data = cursor.execute(f'SELECT * FROM users WHERE telegramid=\'{str(event.sender_id)}\'').fetchone()
        print('first step')
        print(f'user\'s id: {event.sender_id}')
        print('user\'s data: ' + str(data))
        print('active sessions: ' + str(active_dialogs))
        if data is None:
            await client.send_message(event.sender, "your id is: " + str(event.sender_id))
        else:
            role = data[2]
            workplace = data[3]
            user_name = data[1]
            if role == "superadmin":
                await client.send_message(event.sender, "select option", buttons=[
                    [Button.inline('Add User')],
                    [Button.inline('Delete user')],
                    [Button.inline('Create company')]
                ])
                active_dialogs.update({str(event.sender_id): 1})
            if role == "admin":
                active_dialogs.update({str(event.sender_id): 1})
                await client.send_message(event.sender, "select option", buttons=[
                    [Button.inline('Add User')],
                    [Button.inline('Delete user')]
                ])
        raise StopPropagation


    @client.on(events.CallbackQuery(data=b'Add User'))      # method that handles "add user" command
    async def addUserHandler(event):
        print('second step')
        print(f'user\'s id: {event.sender_id}')
        print('active sessions: ' + str(active_dialogs))
        print('here new user\'s instance created')
        users[event.sender_id] = {}
        active_dialogs.update({str(event.sender_id): 11})
        await event.respond("input user id:")
        raise StopPropagation


    @client.on(events.CallbackQuery(data=b'Delete user'))   # method that handles "delete user" command
    async def deleteUserHandler(event):
        # getting all users as list
        active_dialogs.update({str(event.sender_id): 31})
        user_buttons = []
        personnel = cursor.execute(f'SELECT username FROM users WHERE company=\'{workplace}\';').fetchall()
        print(str(personnel))
        for person in personnel:
            if person[0] != user_name:
                user_buttons.append(Button.inline(person[0]))
        await client.send_message(event.sender, "select user to delete:", buttons=user_buttons)
        raise StopPropagation


    @client.on(events.CallbackQuery(data=b'Create company'))    # method that handles "create company" command
    async def createCompanyHandler(event):
        active_dialogs.update({str(event.sender_id): 21})
        await event.respond("input company name:")
        raise StopPropagation


    @client.on(events.CallbackQuery(data=b'return to start'))
    async def returnHandler(event):
        active_dialogs.pop(str(event.sender_id))
        await startHandler(event)
        raise StopPropagation


    @client.on(events.CallbackQuery(data=b'continue'))
    async def continueHandler(event):
        await createCompanyHandler(event)
        raise StopPropagation


    @client.on(events.CallbackQuery(func=lambda e: active_dialogs[str(e.sender_id)] == 13))
    async def chooseCompanyHandler(event):
        users[event.sender_id].update({"company": event.data.decode("utf-8")})
        print('fifth step')
        print(f'user\'s id: {event.sender_id}')
        print('active sessions: ' + str(active_dialogs))
        print('user instances: ' + str(users))
        active_dialogs.update({str(event.sender_id): 14})
        await client.send_message(event.sender, "choose role:", buttons=[
            [Button.inline('admin')],
            [Button.inline('user')]
        ])
        raise StopPropagation


    @client.on(events.CallbackQuery(func=lambda e: active_dialogs[str(e.sender_id)] == 14))
    async def writeDataHandler(event):
        print('sixth step')
        print(f'user\'s id: {event.sender_id}')
        print('active sessions: ' + str(active_dialogs))
        print('user instances: ' + str(users))
        try:
            if role == "superadmin":
                user_role = event.data.decode("utf-8")
                cursor.execute(f'INSERT INTO users VALUES (\'{users[event.sender_id]["telegram_id"]}\', \'{users[event.sender_id]["username"]}\', \'{user_role}\', \'{users[event.sender_id]["company"]}\');')
                database.commit()
                print("writing data OK")
                users.pop(event.sender_id)
                await client.send_message(event.sender, "data recorded successfully!", buttons=[
                    [Button.inline('return to start')]
                ])
            if role == "admin":
                user_role = event.data.decode("utf-8")
                cursor.execute(f'INSERT INTO users VALUES (\'{users[event.sender_id]["telegram_id"]}\', \'{users[event.sender_id]["username"]}\', \'{user_role}\', \'{workplace}\');')
                database.commit()
                print("writing data OK")
                users.pop(event.sender_id)
                await client.send_message(event.sender, "data recorded successfully!", buttons=[
                    [Button.inline('return to start')]
                ])
        except:
            print("error recording data: ")
            await event.respond("data recording failure")
        raise StopPropagation


    @client.on(events.CallbackQuery(func=lambda e: active_dialogs[str(e.sender_id)] == 31))
    async def deleteHandler(event):
        try:
            name = event.data.decode("utf-8")
            cursor.execute(f'DELETE FROM users WHERE username=\'{name}\';')
            database.commit()
            await client.send_message(event.sender_id, "data deleted, what\'s next?", buttons=[
                [Button.inline('continue')],
                [Button.inline('return to start')]
            ])
        except:
            print("error occurred")
        raise StopPropagation


    @client.on(events.NewMessage(func=lambda e: active_dialogs[str(e.sender_id)] == 11))     # method that handles user's input
    async def idInputHandler(event):
        users[event.sender_id].update({"telegram_id": event.text})
        print('third step')
        print(f'user\'s id: {event.sender_id}')
        print('active sessions: ' + str(active_dialogs))
        print('user instances: ' + str(users))
        active_dialogs.update({str(event.sender_id): 12})
        await event.respond("input username:")
        raise StopPropagation


    @client.on(events.NewMessage(func=lambda e: active_dialogs[str(e.sender_id)] == 12))
    async def usernameInputHandler(event):
        users[event.sender_id].update({"username": event.text})
        print('fourth step')
        print(f'user\'s id: {event.sender_id}')
        print('active sessions: ' + str(active_dialogs))
        print('user instances: ' + str(users))
        global office
        print(role)
        if role == "superadmin":
            active_dialogs.update({str(event.sender_id): 13})
            office = cursor.execute(f'SELECT name FROM companies').fetchall()
            print(office[1][0])
            company_buttons = []
            for company in office:
                print("company: " + str(company[0]))
                company_buttons.append(Button.inline(company[0]))
            await client.send_message(event.sender, "choose company:", buttons=company_buttons)
            raise StopPropagation
        elif role == "admin":
            active_dialogs.update({str(event.sender_id): 14})  # need to add admin's company by default
            users[event.sender_id].update({"company": workplace})
            await client.send_message(event.sender, "choose role:", buttons=[
                [Button.inline('admin')],
                [Button.inline('user')]
            ])
            raise StopPropagation


    @client.on(events.NewMessage(func=lambda e: active_dialogs[str(e.sender_id)] == 21))
    async def companyCreationHandler(event):
        try:
            cursor.execute(f'INSERT INTO companies VALUES (\'{event.text}\');')
            database.commit()
            await client.send_message(event.sender, "select option:", buttons=[
                [Button.inline('continue')],
                [Button.inline('return to start')]
            ])
        except:
            print("error occurred")
        raise StopPropagation


    client.run_until_disconnected()
