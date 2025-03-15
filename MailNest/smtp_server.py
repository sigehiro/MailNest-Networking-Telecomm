import asyncio
from aiosmtpd.controller import Controller

class CustomSMTP:
    async def handle_DATA(self, server, session, envelope):
        try:
            print('Message from:', envelope.mail_from)
            print('Message for:', envelope.rcpt_tos)
            print('Message data:\n', envelope.content.decode())

            print('Processing email...')
            return '250 Message accepted for delivery'
        except Exception as e:
            print(f"Error while processing email: {str(e)}")
            return '550 Error processing email'

if __name__ == '__main__':
    controller = Controller(CustomSMTP(), hostname='localhost', port=2525)
    controller.start()
    print("SMTP Server running on localhost:2525")
    
    try:
        asyncio.get_event_loop().run_forever()
    except KeyboardInterrupt:
        controller.stop()
