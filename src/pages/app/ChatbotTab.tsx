import { useEffect, useState } from "react";
import { wsService } from "../../services/websocket";

export default function ChatbotTab() {
  const [dataList, setDataList] = useState<any[]>([]);
  const [inputText, setInputText] = useState("");

  useEffect(() => {
    // Ensure WebSocket is connected when opening Chat tab
    wsService.connect();

    // Listen for incoming live records
    const unsubscribe = wsService.subscribe((message) => {
      console.log("New message received via WS:", message);
      if (message.event === "NEW_RECORD") {
        setDataList((prev) => [message.data, ...prev]);
      }
    });

    return () => unsubscribe();
  }, []);

  const handleSendData = (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputText.trim()) return;

    const payload = {
      message: inputText,
      time: new Date().toLocaleTimeString(),
      source: typeof window !== 'undefined' && !!(window as any).Capacitor?.isNativePlatform() ? "Mobile App" : "Web Browser"
    };

    // Send via WebSocket to server (which broadcasts to phone/app)
    wsService.send(payload);

    setInputText("");
  };

  return (
    <div style={{ padding: "20px", color: "#333", fontFamily: "sans-serif" }}>
      <h2>🤖 Live AutoBiz AI Chat & Sync</h2>

      <form onSubmit={handleSendData} style={{ marginBottom: "20px" }}>
        <input
          type="text"
          value={inputText}
          onChange={(e) => setInputText(e.target.value)}
          placeholder="Enter message or prompt..."
          style={{
            padding: "10px",
            width: "60%",
            borderRadius: "6px",
            border: "1px solid #ccc",
            marginRight: "8px",
          }}
        />
        <button
          type="submit"
          style={{
            padding: "10px 20px",
            backgroundColor: "#2563eb",
            color: "#fff",
            border: "none",
            borderRadius: "6px",
            cursor: "pointer",
            fontWeight: "bold"
          }}
        >
          Send
        </button>
      </form>

      <h3>Live Feed Stream:</h3>
      <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
        {dataList.length === 0 ? (
          <p style={{ color: "#888" }}>No messages yet. Send one from website or app!</p>
        ) : (
          dataList.map((item, index) => (
            <div
              key={index}
              style={{
                padding: "12px",
                background: "#f3f4f6",
                borderRadius: "8px",
                borderLeft: "4px solid #2563eb",
              }}
            >
              <strong>[{item.source || "System"}] ({item.time}):</strong> {item.message}
            </div>
          ))
        )}
      </div>
    </div>
  );
}