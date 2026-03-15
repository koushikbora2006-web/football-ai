async function sendMessage(){

    let input = document.getElementById("user-input")
    let message = input.value

    if(message.trim() === "") return

    let chatBox = document.getElementById("chat-box")

    chatBox.innerHTML += `<div class="user"><b>You:</b> ${message}</div>`

    input.value = ""

    const response = await fetch("/chat", {
        method:"POST",
        headers:{
            "Content-Type":"application/json"
        },
        body:JSON.stringify({message:message})
    })

    const data = await response.json()

    chatBox.innerHTML += `<div class="bot"><b>Bot:</b> ${data.reply}</div>`

    chatBox.scrollTop = chatBox.scrollHeight
}