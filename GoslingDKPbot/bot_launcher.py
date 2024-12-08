import asyncio

async def run_bot_3330():
    proc = await asyncio.create_subprocess_exec('python', './3330/bot3330.py')
    await proc.wait()
    
async def main():
    # Параллельный запуск двух ботов
    await asyncio.gather(run_bot_3330(), run_bot_3344())

# Запуск событийного цикла
asyncio.run(main())
