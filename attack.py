import asyncio
import aiohttp
import time
from uuid import UUID

API_URL = "http://localhost:8000/api"

async def book_seat(session, seat_id, user_id):
    payload = {
        "seat_id": str(seat_id),
        "user_identifier": f"user_{user_id}@test.com"
    }
    try:
        async with session.post(f"{API_URL}/book/safe", json=payload) as resp:
            status = resp.status
            text = await resp.text()
            return status
    except Exception as e:
        return 500

async def run_attack():
    print("🚀 Начинаем атаку на сервер...")
    
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{API_URL}/events") as resp:
            data = await resp.json()
            try:
                target_seat_id = data[0]['seats'][0]['id']
                print(f"🎯 Цель захвачена: Место {target_seat_id}")
            except IndexError:
                print("❌ Нет мест! Сначала выполни /api/init_db")
                return

        tasks = []
        start_time = time.time()
        
        print(f"⚡ Отправляем 50 запросов одновременно...")
        for i in range(50):
            tasks.append(book_seat(session, target_seat_id, i))
        
        results = await asyncio.gather(*tasks)
        end_time = time.time()

        success_count = results.count(200)
        conflict_count = results.count(409)
        error_count = len(results) - success_count - conflict_count
        
        print("\n📊 Результаты атаки:")
        print(f"✅ Успешных броней: {success_count} (Должна быть 1)")
        print(f"🛡️ Отклонено (занято): {conflict_count}")
        print(f"💀 Ошибок сервера: {error_count}")
        print(f"⏱️ Время: {end_time - start_time:.2f} сек")
        
        if success_count == 1:
            print("\n🏆 ТЕСТ ПРОЙДЕН! Race condition побежден.")
        else:
            print(f"\n💥 ПРОВАЛ! Продано {success_count} билетов на одно место.")

if __name__ == "__main__":
    asyncio.run(run_attack())