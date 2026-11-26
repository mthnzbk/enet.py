# ENet Python (zpl-c/enet Python Bağlayıcıları)

[zpl-c/enet](https://github.com/zpl-c/enet) C kütüphanesi için modern, yüksek performanslı ve Pythonik bağlayıcı (binding) kütüphanesi.

ENet, UDP protokolü üzerinde güvenilir (reliable), sıralı (in-order) veya sırasız (unsequenced) paket iletimi, parçalama (fragmentation) ve çoklu kanal (channel) mimarisi sunan hafif bir ağ kütüphanesidir. Özellikle çok oyunculu (multiplayer) oyunlar ve gerçek zamanlı simülasyonlar için standarttır.

Bu bağlayıcı, `zpl-c/enet` çatalının sunduğu yenilikleri (tam entegre IPv6 desteği, monotonik zamanlayıcı, güvenli özellik erişimleri) Python dünyasına taşır ve klasik `pyenet` kütüphanesiyle API uyumluluğu sağlar.

---

## Özellikler

* **Entegre IPv6 & IPv4 Çift Yığın (Dual-Stack):** `zpl-c/enet` altyapısı sayesinde hem IPv4 hem de IPv6 adresleri sorunsuz çalışır.
* **Güvenilir & Güvensiz Paket Gönderimi:** `PACKET_FLAG_RELIABLE`, `PACKET_FLAG_UNSEQUENCED` ve parçalanmış paket desteği.
* **Çoklu Kanal Mimarisi:** Farklı veri akışları için bağımsız mantıksal kanallar (0-255).
* **Pythonik Nesne Yönelimli API:** `Host`, `Peer`, `Packet`, `Address`, `Event` sınıfları ve context manager (`with enet.Host(...)`) desteği.
* **Otomatik Bellek Yönetimi:** Paket ve oturum belleklerinin güvenli biçimde temizlenmesi (`__del__` ve `destroy()`).
* **Sıfır Harici Derleme Bağımlılığı:** Windows x64 için hazır derlenmiş native kütüphane (`enet.dll`) paket içerisinde gelir; Linux ve macOS için tek tıkla derlenebilir (`build_native.py`).

---

## Kurulum

Projeyi doğrudan çalışma dizininize dahil edebilir (`import enet`) veya pip ile kurabilirsiniz:

```bash
# PyPI üzerinden kurulum
pip install enet2

# Geliştirici / düzenlenebilir modda kurulum
pip install -e .
```

---

## Hızlı Başlangıç (Quickstart)

### 1. Sunucu (Server) Örneği

```python
import enet

# Wildcard (0.0.0.0 / ::) adresinde 12345 portunu dinle
server_address = enet.Address(None, 12345)

with enet.Host(server_address, peer_count=32, channel_limit=2) as server:
    print(f"Sunucu başlatıldı: {server_address}")

    running = True
    while running:
        event = server.service(timeout_ms=50)

        if event.type == enet.EVENT_TYPE_CONNECT:
            print(f"[+] İstemci bağlandı: {event.peer.address} (ID: {event.peer.id})")
            event.peer.data = {"username": "Misafir"}

        elif event.type == enet.EVENT_TYPE_RECEIVE:
            mesaj = event.packet.data.decode("utf-8")
            print(f"<- Gelen paket [{event.channel_id}]: {mesaj}")

            # Yanıt paketi gönder
            yanit = f"Echo: {mesaj}".encode("utf-8")
            event.peer.send(event.channel_id, enet.Packet(yanit, enet.PACKET_FLAG_RELIABLE))
            server.flush()

        elif event.type in (enet.EVENT_TYPE_DISCONNECT, enet.EVENT_TYPE_DISCONNECT_TIMEOUT):
            print(f"[-] İstemci ayrıldı: {event.peer.address}")
```

### 2. İstemci (Client) Örneği

```python
import time
import enet

# İstemci host'u oluştur (yerel porta bağlanmaz, giden bağlantı açar)
with enet.Host(None, peer_count=1, channel_limit=2) as client:
    hedef = enet.Address("127.0.0.1", 12345)
    peer = client.connect(hedef, channel_count=2, data=100)

    # Bağlantı kurulmasını bekle
    connected = False
    start = time.time()
    while time.time() - start < 5.0:
        event = client.service(timeout_ms=50)
        if event.type == enet.EVENT_TYPE_CONNECT:
            connected = True
            print(f"[+] Sunucuya bağlanıldı! RTT: {peer.round_trip_time}ms")
            break

    if connected:
        # Güvenilir (reliable) paket gönder
        paket = enet.Packet(b"Merhaba ENet!", enet.PACKET_FLAG_RELIABLE)
        peer.send(channel_id=0, packet=paket)
        client.flush()

        # Yanıt bekle
        start = time.time()
        while time.time() - start < 2.0:
            event = client.service(timeout_ms=50)
            if event.type == enet.EVENT_TYPE_RECEIVE:
                print(f"<- Sunucudan gelen: {event.packet.data.decode('utf-8')}")
                break

        # Nazikçe bağlantıyı kes
        peer.disconnect(data=0)
        client.flush()
```

---

## API Referansı

### `enet.Address(host: str | None = None, port: int = 0)`
Bir ağ adresini (IP / alan adı ve port) temsil eder.
* `host`: IP adresi ("127.0.0.1", "::1"), alan adı veya `None` (tüm arayüzler).
* `port`: Port numarası (0-65535).
* `ip`: Düzeltilmiş IP adresi dizesi.
* `is_ipv6`: Native IPv6 adresi olup olmadığı (`bool`).
* `is_any`: Wildcard / dinleme adresi olup olmadığı (`bool`).

### `enet.Host(address, peer_count=32, channel_limit=2, incoming_bandwidth=0, outgoing_bandwidth=0)`
Bağlantıları yöneten ana ENet host sınıfı.
* `service(timeout_ms=0) -> Event`: Ağ olaylarını bekler ve döndürür.
* `poll(timeout_ms=0) -> Iterator[Event]`: Tüm bekleyen olayları yield eden üreteç.
* `connect(address: Address, channel_count=2, data=0) -> Peer`: Yeni bir bağlantı başlatır.
* `broadcast(channel_id: int, packet: Packet)`: Bağlı tüm peer'lara paketi dağıtır.
* `flush()`: Kuyruktaki paketleri hemen gönderir.
* `destroy()`: Host'u kapatır ve soketi serbest bırakır.
* Özellikler: `peers_count`, `packets_sent`, `packets_received`, `bytes_sent`, `bytes_received`, `mtu`.

### `enet.Peer`
Bağlantı kurulan uzak düğümü (istemci veya sunucu) temsil eder.
* `send(channel_id: int, packet: Packet) -> int`: Belirtilen kanala paket kuyruklar.
* `receive() -> tuple[int, Packet] | None`: Alınan paketi ve kanalını çeker.
* `ping()`: RTT ölçümü ve bağlantı canlılığı için ping gönderir.
* `disconnect(data=0)`: Nazik bağlantı kesme isteği gönderir.
* `disconnect_now(data=0)`: Hemen bağlantıyı sonlandırır.
* `disconnect_later(data=0)`: Bekleyen paketler iletildikten sonra bağlantıyı sonlandırır.
* `data`: Kullanıcının bu peer ile ilişkilendirebileceği özel Python verisi (örn. `peer.data = {"player_id": 5}`).
* Özellikler: `id`, `address`, `state`, `round_trip_time` (RTT), `packets_sent`, `packets_lost`, `packet_loss`, `bytes_sent`, `bytes_received`.

### `enet.Packet(data: bytes | str, flags: int = PACKET_FLAG_RELIABLE)`
Ağ üzerinden iletilen veri paketi.
* `data`: Bayt (`bytes`) cinsinden veri.
* `data_length`: Veri uzunluğu.
* `flags`: Paket bayrakları (`PACKET_FLAG_RELIABLE`, `PACKET_FLAG_UNSEQUENCED`, vb.).
* `reliable`: Paketin güvenilir olup olmadığı.
* `destroy()`: Paketi bellekten temizler.

### `enet.Event`
`host.service()` tarafından döndürülen ağ olayı.
* `type`: Olay tipi (`EVENT_TYPE_CONNECT`, `EVENT_TYPE_RECEIVE`, `EVENT_TYPE_DISCONNECT`, `EVENT_TYPE_NONE`).
* `peer`: Olayın ait olduğu `Peer` nesnesi.
* `channel_id` (veya `channelID`): Olayın gerçekleştiği kanal numarası.
* `data`: Bağlantı veya ayrılma ile ilişkili kullanıcı verisi.
* `packet`: `EVENT_TYPE_RECEIVE` durumunda alınan `Packet` nesnesi.

---

## Testleri Çalıştırma

Kütüphanenin tüm birim testlerini `pytest` ile çalıştırabilirsiniz:

```bash
pytest tests/ -v
```

---

## Lisans

Bu proje MIT lisansı altında lisanslanmıştır. Orijinal ENet telif hakkı Lee Salzman, zpl-c/enet telif hakkı Vladyslav Hrytsenko ve Dominik Madarász'a aittir.
