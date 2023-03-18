function addToCart(id, add){
    console.log(id)
    console.log(add)
    if( user === 'AnonymousUser'){
        console.log('User not authenticated')
    }
    else{
        updateOrder(id, add)
    }
}

function updateOrder(productId, action){
    var url = 'update_item'

    fetch(url, {
        method: 'POST',
        headers:{
            'Content-Type': 'application/json',
            'X-CSRFToken': csrftoken,
        },
        body:JSON.stringify({'product_id': productId, 'action': action})
    })
    .then((response) =>{
        return response.json()
    })
    .then((data) =>{
        console.log('data:', data)
    })
}
