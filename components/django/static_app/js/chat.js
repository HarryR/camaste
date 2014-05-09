"use strict";

/*
 a88888b. dP                  dP   
d8'   `88 88                  88   
88        88d888b. .d8888b. d8888P 
88        88'  `88 88'  `88   88   
Y8.   .88 88    88 88.  .88   88   
 Y88888P' dP    dP `88888P8   dP   
*/

var Camaste_Chat = Stapes.subclass({
	constructor: function (app, $element) {
		this.app = app;
		this.$el = $($element);

		var self = this;
		app.on('ready', function(){
			self.connect();
			$('.input-text', $element).focus();
			self.scroll_to_bottom();
		});
		app.on('chat.msg', function(msg){
			self.add_line(msg.body.text)
		});

		$('.input-send', this.$el).on('click', function () {
			self.input_submit();
		});

		$('.input-text', this.$el).on('keypress', function(e) {
			var code = e.keyCode || e.which;
			if(code == 13) { //Enter keycode
				self.input_submit();
			}
		});
	},

	connect: function () {
		this.app.realtime.call('chat.join', {
			"token": "test"
		});
	},

	input_submit: function () {
		var $input = $('input.input-text', this.$el);
		var val = $input.val().trim();
		if( val === "" ) {
			return;
		}

		var message = $('<span />').append( $('<span />').addClass('username').text('You Wrote') )
								   .append( $('<span />').addClass('text').text(val) );
		$input.val('').focus();
		//this.add_line(message);

		this.app.realtime.call('chat.sendmsg', {
			"token": "test",
			"text": val
		});
	},

	scroll_to_bottom: function () {
		var $history = $('.history', this.$el);
		$history.scrollTop($history.prop('scrollHeight'));
	},	

	/**
	 * Add a line of HTMl to the buffer.
	 */
	add_line: function (html) {
		var $ul = $('.history-lines', this.$el);
		// Restrict to 100 lines at a time
		if( $('li', $ul).length > 100 ) {
			$('li:first-child', $ul).remove();
		}

		$ul.append($('<li />').html(html));
		this.scroll_to_bottom();
	},
});

new Camaste_Chat(Camaste, $('#chat'));