import asyncio

async def run_bot():
    proc = await asyncio.create_subprocess_exec('python', './3330/bot3330.py')
    await proc.wait()
    
async def main():
    await asyncio.gather(run_bot())

# Запуск событийного цикла
asyncio.run(main())
