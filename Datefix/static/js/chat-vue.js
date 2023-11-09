// import Swal from "/sweetalert2.min.js";



var app = new Vue({
  delimiters: ["[[", "]]"],
  el: "#app",
  name: "chat",
  data: {
    messages: [],
    chat_threads: [],
    chat_messages: [],
    chat_object: {},
    chat_id: "",
    chat_room: "",
    message: "",
    user: "",
    id: "",
    loggedInUser: "",
    activeUser: "",
    loading: true,
    status: "",
    messageStatus: "",
    approving: false,
    message_id: "",
    typing: false,
    expiredUsers: [],
    response: "",
    usernames: {},
    showResponse: false,
    acceptRequestName: "",
  },
  async mounted() {
    this.id = this.$refs.userID.value;
    await this.getUser();
    await this.getAllChats();
    const url = get_url();
    this.socket = new WebSocket(url);
    await this.websocket();
    this.modalStatic();
  },
  // beforeDestroy() {
  //   this.disconnect(this.chat_object);
  // },
  methods: {
    modalStatic() {
      if (this.expiredUsers.length > 0) {
        setTimeout(() => {
          $("#expiredModal").modal({
            show: true,
            backdrop: "static",
          });
        }, 200);
      }
    },
    get_id(user) {
      this.chat_object = user;
      this.chat_id = user.chat_id;
    },
    async websocket() {
      this.socket.onclose = (e) => {
      };

      this.socket.onopen = (e) => {
      };

      this.socket.onerror = (e) => {
      };

      this.socket.onmessage = (e) => {
        this.chat_messages.push(JSON.parse(e.data));
        this.getSingleChat(this.chat_object);
        let data = JSON.parse(e.data);

        if (data.function === "connect" && data.action === "accept") {
          this.sendAccept(data.chat_room);
        }

        if (data.function === "connect" && data.action === "jilt") {
          this.sendJilt(data.chat_room);
        }

        if (data.function === "connect") {
          this.chat_room = data.chat_room;
        }
        if (data.username !== this.loggedInUser && data.function === "login") {
          this.getAllChats();
        }
        if (
          data.username !== this.loggedInUser &&
          data.function === "message"
        ) {
          this.message_id = data.message_id;
          this.messageStatus = data.status;
          scroll()
        }
        if (data.username === this.loggedInUser && data.function === "accept") {
          if (data.result.response !== undefined) {
            $("#acceptModal").modal("hide");
            $("#expiredModal").modal("hide");
            // this.showResponse = true;
            // this.response = data.result.response;
            // alert(data.result.response);
            //   setTimeout(() => {
            //     this.showResponse = false;
            //   }, 3000);
            //   location.reload();
            // }
          }
          if (data.result.couple_id !== undefined) {
            location.reload();
          }
        }

        if (data.username !== this.loggedInUser && data.function === "accept") {
          if (data.result.couple_id !== undefined) {
            location.reload();
          }
          if (data.result.response !== undefined) {
            // const result = confirm(
            //   data.username +
            //     " has accepted to keep chatting with you. Accept or Jilt"
            // );
            this.acceptRequestName = data.username;
            this.chat_room = data.chat_room;
            this.chat_id = data.chat_id;
            this.$refs.finalAccept.click();
            // if (result) {
            //   this.sendAccept2(data.chat_room, data.chat_id);
            // } else {
            //   this.jilt();
            // }
          }
        }
        // if (
        //   this.chat_threads.some((val) => val.username == data.username) &&
        //   data.function === "accept"
        // ) {
        //   $("#acceptModal").modal("show");
        // }
        // // if (data.username == this.loggedInUser && data.function === "accept") {
        //   this.response = data.result.response;
        //   this.$refs.close.click();
        // }
        if (data.result === "succeed" && data.function === "jilt") {
          location.reload();
        }
      };
    },
    async getUser() {
      try {
        await fetch(`/chat/api/user/${this.id}`)
          .then((response) => response.json())
          .then((data) => {
            if (data !== "None") {
              this.user = data;
              this.loggedInUser = data.username;
            }
          });
      } catch (error) {
      }
    },
    async getAllChats() {
      try {
        await fetch(`/chat/api/threads`)
          .then((response) => response.json())
          .then((data) => {
            this.chat_threads = data.chat_threads.filter(
              (chat_thread) => chat_thread.expired == false
            );
            let expiredUsers = data.chat_threads.filter(
              (expiredUser) => expiredUser.expired == true
            );
            this.expiredUsers = expiredUsers;
            if (expiredUsers.length > 0) {
              this.$refs.expired.click();
            }
          });
      } catch (error) {
      }
    },
    async getSingleChat(chat) {
      try {
        await fetch(`/chat/api/chat/${chat.chat_id}`)
          .then((response) => response.json())
          .then((data) => {
            this.chat_id = data.chat_id;
            this.status = data.status;
            this.chat_messages = data.chat_list;
            scroll()
          });
        this.loading = false;
      } catch (error) {
      }
    },
    connect(chat) {
      this.chat_object = chat;
      this.activeUser = chat.username;
      let connect_thread = {
        username: this.loggedInUser,
        chat_id: chat.chat_id,
        function: "connect",
      };
      this.socket.send(JSON.stringify(connect_thread));
      show_chat()
    },
    connect_final(chat, action) {
      this.chat_object = chat;
      this.activeUser = chat.username;
      let connect_thread = {
        username: this.loggedInUser,
        chat_id: chat.chat_id,
        action: action,
        function: "connect",
      };
      this.socket.send(JSON.stringify(connect_thread));
    },
    disconnect() {
      let disconnect_thread = {
        username: this.loggedInUser,
        chat_id: this.chat_id,
        function: "disconnect",
      };
      this.socket.send(JSON.stringify(disconnect_thread));
    },
    sendMessage() {
      let thread_obj = {
        sender_id: this.id,
        message: this.message,
        sender: this.loggedInUser,
        function: "message",
      };
      this.socket.send(JSON.stringify(thread_obj));
      this.message = "";
    },
    jilt() {
      this.connect_final(this.chat_object, "jilt");
    },
    accept() {
      this.connect_final(this.chat_object, "accept");
    },

    sendJilt(chat_room) {
      let jilt_thread = {
        username: this.loggedInUser,
        chat_room: this.chat_room,
        function: "jilt",
      };
      this.socket.send(JSON.stringify(jilt_thread));
      this.$refs.close.click();
    },
    sendAccept(chat_room) {
      let accept_thread = {
        username: this.loggedInUser,
        chat_room: chat_room,
        function: "accept",
      };
      this.socket.send(JSON.stringify(accept_thread));
      this.$refs.close.click();
    },
    sendAccept2() {
      let accept_thread = {
        username: this.loggedInUser,
        chat_room: this.chat_room,
        function: "accept",
        chat_id: this.chat_id,
      };
      this.socket.send(JSON.stringify(accept_thread));
      this.$refs.close.click();
    },
    isDelivered() {
      let isDelivered_thread = {
        message_id: this.message_id,
        function: "isDelivered",
      };
      this.socket.send(JSON.stringify(isDelivered_thread));
    },
    deleteForAll() {
      let deleteForAll_thread = {
        username: this.loggedInUser,
        function: "deleteForAll",
      };
      this.socket.send(JSON.stringify(deleteForAll_thread));
    },

  },

});

function scroll(){
  try {
    const k = document.getElementsByClassName('screen')
    k[k.length - 1].scrollIntoView()
  }catch (e){

  }
}

function get_url(){
  const origin = window.location.origin
  let wss_scheme = 'ws'
  if (origin.startsWith('https')){
    wss_scheme = 'wss'
  }
  return `${wss_scheme}://127.0.0.1:8001/chat/`

}

function back_ (){
  let device = window.devicePixelRatio
  let arrow_ = document.getElementById('arrow')
  let contacts_ = document.getElementById('contact_list')
  let chats_ = document.getElementById('chat_list')
  if (device > 1.100000023841858){
    chats_.classList.remove('d-block')
    contacts_.classList.remove('d-none')
    arrow_.classList.add('d-none')
  }
}

function show_chat() {
  let arrow_ = document.getElementById('arrow')
  let contacts_ = document.getElementById('contact_list')
  let chats_ = document.getElementById('chat_list')
  let device = window.devicePixelRatio
  if (device > 1.100000023841858) {
    contacts_.classList.add('d-none')
    chats_.classList.add('d-block')
    arrow_.classList.remove('d-none')
  }

}