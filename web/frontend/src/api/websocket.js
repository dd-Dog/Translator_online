/**
 * WebSocket客户端
 */
export class WebSocketClient {
  constructor(url) {
    this.url = url
    this.ws = null
    this.reconnectAttempts = 0
    this.maxReconnectAttempts = 5
    this.reconnectDelay = 1000
    this.listeners = {}
  }
  
  connect() {
    return new Promise((resolve, reject) => {
      try {
        this.ws = new WebSocket(this.url)
        
        this.ws.onopen = () => {
          console.log('WebSocket连接已建立')
          this.reconnectAttempts = 0
          resolve()
        }
        
        this.ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data)
            this.handleMessage(data)
          } catch (e) {
            console.error('解析WebSocket消息失败:', e)
          }
        }
        
        this.ws.onerror = (error) => {
          console.error('WebSocket错误:', error)
          reject(error)
        }
        
        this.ws.onclose = () => {
          console.log('WebSocket连接已关闭')
          this.attemptReconnect()
        }
      } catch (error) {
        reject(error)
      }
    })
  }
  
  handleMessage(data) {
    const { type } = data
    if (this.listeners[type]) {
      this.listeners[type].forEach(callback => callback(data))
    }
    if (this.listeners['*']) {
      this.listeners['*'].forEach(callback => callback(data))
    }
  }
  
  on(type, callback) {
    if (!this.listeners[type]) {
      this.listeners[type] = []
    }
    this.listeners[type].push(callback)
  }
  
  off(type, callback) {
    if (this.listeners[type]) {
      this.listeners[type] = this.listeners[type].filter(cb => cb !== callback)
    }
  }
  
  send(data) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data))
    }
  }
  
  close() {
    if (this.ws) {
      this.ws.close()
      this.ws = null
    }
  }
  
  attemptReconnect() {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++
      setTimeout(() => {
        console.log(`尝试重连 (${this.reconnectAttempts}/${this.maxReconnectAttempts})...`)
        this.connect().catch(() => {
          // 重连失败，继续尝试
        })
      }, this.reconnectDelay * this.reconnectAttempts)
    }
  }
}

