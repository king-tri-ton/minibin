# Minibin - Утилита для Очистки Корзины в Windows 10

![MiniBin](banner.png)

---

![Downloads](https://img.shields.io/github/downloads/king-tri-ton/minibin/total)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
![Platform](https://img.shields.io/badge/platform-Windows_10-lightgrey)
![Python Version](https://img.shields.io/badge/python-3.7%2B-blue)
[![All Contributors](https://img.shields.io/badge/all_contributors-3-orange.svg?style=flat-square)](#contributors)

## Особенности

* **Очистка всех дисков**: Утилита очищает корзину не только на диске C, но и на всех остальных логических дисках (E, B, D и т.д.).
* **Скрывать уведомления**: Добавлено меню «Скрывать уведомления» - данная настройка позволяет скрыть уведомление об успешной очистке корзины.
* **Динамическая иконка в трее**: Программа динамически отображает статус корзины в иконке в системном трее.
* **Интеграция с автозагрузкой**: Вы можете добавить исполняемый файл `minibin-kt.exe` в папку "автозагрузка", чтобы Minibin запускался вместе с системой.

## Установка

1. Скачайте последний релиз из [репозитория](https://github.com/king-tri-ton/minibin/releases).
2. Разархивируйте архив в удобное место на вашем компьютере.
3. При желании, переместите файл `minibin-kt.exe` в папку "автозагрузка".

## Использование

1. Запустите программу, выполнив `minibin-kt.exe`.
2. Щёлкните правой кнопкой мыши на иконке в трее для отображения доступных опций:

   * **Открыть корзину** - открыть стандартное окно корзины.
   * **Очистить корзину** - удалить все файлы из корзины на всех дисках.
   * **Скрывать уведомление** - включить или выключить уведомления об успешной очистке.
   * **Выход** - закрыть программу.
3. Если уведомления включены, после очистки корзины появится уведомление о успешной очистки корзины.

## Информация о Ярлыке Корзины

Если вы хотите избавиться от ярлыка корзины на рабочем столе, вы можете следовать инструкциям на [remontka.pro](https://remontka.pro/remove-recycle-bin-windows/).

---

## Примечание по удалению

Minibin сохраняет свои настройки (например, скрытие уведомлений) в реестре Windows в ключе:

```
HKEY_CURRENT_USER\Software\MiniBinKT
```

Если вы удаляете программу, записи в реестре останутся. Чтобы полностью удалить настройки, можно вручную удалить этот ключ с помощью редактора реестра (`regedit`) или специального скрипта очистки.

---

## Contributors

<table>
  <tbody>
    <tr>
      <td align="center" valign="top" width="20%">
        <a href="https://github.com/king-tri-ton">
          <img src="https://avatars.githubusercontent.com/king-tri-ton?s=100" width="100px;" alt="king-tri-ton"/><br />
          <sub><b>king-tri-ton</b></sub>
        </a><br />
        Автор проекта
      </td>
      <td align="center" valign="top" width="20%">
        <a href="https://github.com/MYRSGRAL">
          <img src="https://avatars.githubusercontent.com/MYRSGRAL?s=100" width="100px;" alt="MYRSGRAL"/><br />
          <sub><b>MYRSGRAL</b></sub>
        </a><br />
        Вклад в разработку
      </td>
      <td align="center" valign="top" width="20%">
        <a href="https://github.com/kobaltgit">
          <img src="https://avatars.githubusercontent.com/kobaltgit?s=100" width="100px;" alt="kobaltgit"/><br />
          <sub><b>kobaltgit</b></sub>
        </a><br />
        Вклад в проект
      </td>
    </tr>
  </tbody>
</table>

---

## Примечание по иконке

Иконка в трее создана [автором](https://github.com/king-tri-ton/) и используется с разрешения.

---

## Лицензия

Проект распространяется по лицензии [MIT](LICENSE).

---

## Контакты

По вопросам и предложениям:

- Telegram: [@king_tri_ton](https://t.me/king_tri_ton)
- Email: [mdolmatov99@gmail.com](mailto:mdolmatov99@gmail.com)
- или создавайте issues

---

by **King Triton**