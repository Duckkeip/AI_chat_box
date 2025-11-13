training_sentences = [
"tạm biệt","bye","hẹn gặp lại","see you","bye bye","chúc bạn một ngày tốt lành","mình đi đây","hẹn gặp lại bạn","tạm biệt nhé","chúc bạn tối vui vẻ"
"mình đi trước nha","bye bạn","tạm biệt bạn nhé","hẹn gặp lại sau","chúc bạn cuối tuần vui vẻ","mình phải đi đây","bye bye nha","tạm biệt mọi người","chúc bạn may mắn","hẹn gặp lại lần sau","mình đi đây nha","tạm biệt bạn thân mến","see ya","bye bye bạn ơi","chúc bạn ngủ ngon","tạm biệt nhé mọi người","mình đi đây nha","bye bạn iu","hẹn gặp lại vào lần tới","chúc bạn một ngày tuyệt vời","mình đi đây nhé","tạm biệt bạn yêu","bye bye nha bạn","hẹn gặp lại nhé bạn","chúc bạn thành công"
]

training_labels = [
"B1","B2","B3","B4","B5","B6","B7","B8","B9","B10",
"B11","B12","B13","B14","B15","B16","B17","B18","B19","B20","B21","B22","B23","B24","B25","B26","B27","B28","B29","B30","B31","B32","B33","B34","B35"
]

responses = {
"B1": ["Tạm biệt! Chúc bạn một ngày vui vẻ."],
"B2": ["Bye! Hẹn gặp lại bạn."],
"B3": ["Hẹn gặp lại! Chúc bạn mọi việc suôn sẻ."],
"B4": ["See you! Hy vọng sớm gặp lại bạn."],
"B5": ["Bye bye! Chúc bạn có một ngày tuyệt vời."],
"B6": ["Chúc bạn một ngày tốt lành! Hẹn gặp lại bạn."],
"B7": ["Mình đi đây! Hẹn gặp lại bạn sau."],
"B8": ["Hẹn gặp lại bạn! Chúc bạn mọi điều tốt đẹp."],
"B9": ["Tạm biệt nhé! Chúc bạn một buổi tối thư giãn."],
"B10": ["Chúc bạn tối vui vẻ! Hẹn gặp lại bạn."],
"B11": ["Mình đi trước nha! Hẹn bạn một ngày vui vẻ."],
"B12": ["Bye bạn! Hẹn sớm gặp lại nha."],
"B13": ["Tạm biệt bạn nhé! Chúc bạn mọi việc thuận lợi."],
"B14": ["Hẹn gặp lại sau! Chúc bạn một buổi tốt lành."],
"B15": ["Chúc bạn cuối tuần vui vẻ! Hẹn gặp lại bạn nha."],
"B16": ["Mình phải đi đây! Hẹn gặp lại nhé."],
"B17": ["Bye bye nha! Chúc bạn một ngày tuyệt vời."],
"B18": ["Tạm biệt mọi người! Chúc cả nhà một ngày tốt lành."],
"B19": ["Chúc bạn may mắn! Hẹn gặp lại nha."],
"B20": ["Hẹn gặp lại lần sau! Chúc bạn một ngày thuận lợi."],
"B21": ["Mình đi đây nha! Hẹn gặp lại bạn."],
"B22": ["Tạm biệt bạn thân mến! Chúc bạn một ngày vui vẻ."],
"B23": ["See ya! Hẹn gặp lại nha."],
"B24": ["Bye bye bạn ơi! Chúc bạn mọi điều tốt đẹp."],
"B25": ["Chúc bạn ngủ ngon! Hẹn gặp lại bạn."],
"B26": ["Tạm biệt nhé mọi người! Chúc mọi người buổi tối an lành."],
"B27": ["Mình đi đây nha! Chúc bạn một ngày tuyệt vời."],
"B28": ["Bye bạn iu! Hẹn gặp lại nha."],
"B29": ["Hẹn gặp lại vào lần tới! Chúc bạn thành công."],
"B30": ["Chúc bạn một ngày tuyệt vời! Hẹn gặp lại nha."],
"B31": ["Mình đi đây nhé! Chúc bạn một ngày vui vẻ."],
"B32": ["Tạm biệt bạn yêu! Hẹn gặp lại nha."],
"B33": ["Bye bye nha bạn! Chúc bạn một ngày tốt lành."],
"B34": ["Hẹn gặp lại nhé bạn! Chúc bạn mọi việc thuận lợi."],
"B35": ["Chúc bạn thành công! Hẹn gặp lại nha."]
}
