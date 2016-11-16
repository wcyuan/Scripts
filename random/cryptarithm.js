//
// These functions attempt to solve Crypto-Arithmetic problems
// "cryptarithm"
// These are arithmetic problems consisting of words, where
// each letter represents a digit, and the goal is to figure
// out which digit each letter represents.
//

function swap(array, ii, jj) {
	var tmp = array[ii];
	array[ii] = array[jj];
	array[jj] = tmp;
}

// Given an array, call the function on all permutations
// of length kk of that array.
// If the function returns true, that means we should stop
// iterating.  Otherwise, if the function returns null
// or false, we'll keep iterating.
function permutations(array, ii, kk, func) {
	if (ii == kk || ii == array.length) {
		return func(array);
	}
	var should_stop = permutations(array, ii+1, kk, func);
	if (should_stop !== null && should_stop) {
		return should_stop;
	}
	for (var jj = ii+1; jj < array.length; jj++) {
		swap(array, ii, jj);
		var should_stop = permutations(array, ii+1, kk, func);
		swap(array, ii, jj);
		if (should_stop !== null && should_stop) {
			return should_stop;
		}
	}
}

function replace_all(string, old_substring, new_substring) {
	return string.split(old_substring).join(new_substring);
}

function substitute(string, mapping) {
	var new_string = string;
	for (var char in mapping) {
		new_string = replace_all(new_string, char, mapping[char]);
	}
	return new_string;
}

function check(expression, mapping) {
	return eval(substitute(expression, mapping));
}

function make_mapping(letters, values) {
	var mapping = {};
	for (var ii = 0; ii < letters.length; ii++) {
		mapping[letters[ii]] = values[ii];
	}
	return mapping;
}

function make_letters(string) {
	var letters = {};
	for (var ii = 0; ii < string.length; ii++) {
		var char = string.charAt(ii);
		if (char >= 'A' && char <= 'Z') {
			letters[char] = 1;
		}
	}
	return Object.keys(letters);
}

// Expression should be an equation, with two equals signs, like:
//   "TSHIRT+SKIRT==CLOTHES"
//
// This is very general (can solve almost any expression)
// but also quite slow.  It checks about 6000 permutations
// per second, so if your expression uses 10 letters, then
// it will take about 10! = 3628800 / 6,000 / 60 = 10 minutes
// to find all solutions.
//
// Currently, this stops after it finds the first solution, and
// it doesn't enforce the rule that the first letter of each
// number must not map to zero.
//
function solve(expression) {
	expression = expression.toUpperCase();
	var letters = make_letters(expression);
	var ntries = 0;
	permutations([0, 1, 2, 3, 4, 5, 6, 7, 8, 9], 0, letters.length, function(values) {
		var mapping = make_mapping(letters, values);
		if (check(expression, mapping)) {
			console.log("GOOD: " + mapping);
			console.log(substitute(expression, mapping));
			return true;
		} else {
			//console.log("BAD: " + mapping);
			//console.log(substitute(expression, mapping));
		}
		ntries += 1;
		if (ntries % 1000 == 0) {
			console.log(Date() + " - " + ntries + " tries.")
		}
	})
}

