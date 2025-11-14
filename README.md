# MachiKoro
tablegame


# Общая структура
```
machi_koro/
├─ README.md
├─ pyproject.toml / requirements.txt
├─ machi_core/          # логика игры (правила, состояние, карты, боты)
│  ├─ __init__.py
│  ├─ cards.py          # описание типов карт и их свойств
│  ├─ state.py          # GameState, PlayerState, вспомогательные структуры
│  ├─ actions.py        # описание возможных действий (ROLL, BUY, BUILD, END_TURN...)
│  ├─ rules.py          # применение действий, смена хода, проверка победы
│  ├─ serialization.py  # перевод состояния/действий в dict и обратно (для UI)
│  ├─ agents.py         # базовый интерфейс Agent (человек/бот)
│  └─ bots/
│     ├─ __init__.py
│     ├─ random_bot.py  # простой случайный бот
│     └─ greedy_bot.py  # жадный бот по простым эвристикам
│
├─ machi_client/        # “клиент игры” — прослойка между логикой и UI
│  ├─ __init__.py
│  ├─ base.py           # интерфейс IGameClient (get_state, send_action и т.п.)
│  └─ local_client.py   # реализация локальной игры (вся логика в памяти)
│
├─ ui/                  # десктоп-интерфейс (PySide6)
│  ├─ __init__.py
│  ├─ main_window.py    # главное окно игры, создание клиентa, обработка событий
│  ├─ game_controller.py# glue-код: связывает UI с IGameClient и агентами
│  └─ widgets/
│     ├─ __init__.py
│     ├─ card_widget.py     # виджет отдельной карты
│     ├─ player_panel.py    # панель игрока (монеты, здания, достопримечательности)
│     ├─ market_view.py     # отображение рынка карт
│     └─ log_panel.py       # (опционально) лог событий/ходов
│
├─ desktop/             # точка входа для настольного приложения
│  └─ main.py           # запуск QApplication, создание MainWindow
│
├─ assets/              # ресурсы (графика/шрифты)
│  ├─ images/
│  │  ├─ cards/         # картинки карт (по id карт из cards.py)
│  │  └─ ui/            # фон стола, иконки монет, кнопок и т.п.
│  └─ fonts/            # (опционально) свои шрифты
│
└─ tests/               # тесты логики игры
   ├─ __init__.py
   ├─ test_rules_basic.py   # тесты базовых правил (доход, покупка, победа)
   └─ test_bots.py          # тесты поведения ботов (делают легальные ходы и т.д.)
```