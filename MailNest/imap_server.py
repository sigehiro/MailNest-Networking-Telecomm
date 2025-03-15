import asyncio
import aiosqlite
from aiosmtpd.controller import Controller

class CustomIMAP:
    async def handle_LOGIN(self, username, password):
        return True  

    async def handle_SELECT(self, mailbox):
        return True  

    async def handle_FETCH(self, message_id):
        #get email from database
        async with aiosqlite.connect('db.sqlite3') as db:  
            async with db.execute("SELECT * FROM mail_email WHERE id=?", (message_id,)) as cursor:
                message = await cursor.fetchone()
                return message  

    async def handle_LIST(self):
        #get list of mailboxes
        return ["INBOX"]  

async def run_imap_server():
    controller = Controller(CustomIMAP(), hostname='localhost', port=993)
    controller.start()
    print("IMAP Server running on localhost:993")
    
    try:
        await asyncio.Event().wait()  
    except KeyboardInterrupt:
        controller.stop()

if __name__ == '__main__':
    asyncio.run(run_imap_server())
