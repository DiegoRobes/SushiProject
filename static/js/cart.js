
// This function gets 2 args from the template and then does one of two things. if the user is no authenticated,
// it just logs the args and gives a little message. however, if the user is authenticated, the second function enters
// in play.
function addToCart(id, action){
    console.log(id)
    console.log(action)
    if( user === 'AnonymousUser'){
        console.log('User not authenticated, cannot create order')
    }
    else{
        updateOrder(id, action)
    }
}

// this func looks complicated, but its actually simple. what is does is a post request to the server
// first it sets the url where the request will be received/handled. then we create the request dictionary
// including method headers and body. This dictionary is an API request to be sent to the server, its contents can be
// accessed as any other dict and we can work with their values in the server.
// check all the code relative to the csrftoken on the base template, it is essential for this thing to work.
// finally, we get a response from the server and out it through the console
function updateOrder(productId, to_do){
    var url = 'update_item'

    fetch(url, {
        method: 'POST',
        headers:{
            'Content-Type': 'application/json',
            'X-CSRFToken': csrftoken,
        },
        body: JSON.stringify({'product_id': productId, 'action': to_do})
    })
    .then((response) =>{
        return response.json()
    })
    .then((data) =>{
        console.log('data:', data)
        location.reload()
    })
}
