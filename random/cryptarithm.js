//
// These functions attempt to solve Crypto-Arithmetic problems
// "cryptarithm"
// These are arithmetic problems consisting of words, where
// each letter represents a digit, and the goal is to figure
// out which digit each letter represents.
//
// Some examples:
//   solve_singleop(["send", "more", "money"])
//   solve_singleop(["nevada", "idaho", "states"])
//   solve_singleop(["tshirt", "skirt", "clothes"])
//


// ---------------------------------------------------------- //

//
// solve_singleop is less general than solve_general, but should
// be faster.  It can handle any number of numbers which are all
// being added together or multiplied together.
//
// Arguments:
//
// words should be an array of strings.
//
// operation should be either "+" or "*".  Note that "*" is not well tested.
//
// callback is a function that will be called on each mapping that satisfies
// the equation.  It will be called with three arguments: the mapping,
// the expression with letters translated to numbers as a string on a single line
// and the expression nicely formatted like
//    9567
//  + 1085
// -------
//   10652
//
// len is an integer that indicates which place value we should be looking
// at.  Users generally should not provide it, it is only for internal use.
// The idea is that in order to satisfy the full expression, first you
// have to satisfy just the units place.  When you just add up the units place
// of all the numbers, and then you take mod 10, you should get the units place
// of the result.  Then, for all the mappings that satisfy the units place,
// you can look for mappings that satisfy the units place and the tens place.
// And so on until you satisfy all places.  Len = 1 means only look at the
// units place.  Len = 2 means look at the units place and tens place.  Etc.
//
// mappings is a hash from a letter to the number that letter represents.
// Users should generally not provide it, it is for internal use, for
// passing around the intermediate mappings that the algorithm is trying
// on recursive calls.
//
function solve_singleop(words, operation, callback, len, mappings) {
	//console.log([words, operation, len, mappings]);

	// Initialization
	if (!mappings) {
		mappings = {};
	}
	if (!len) {
		words = words.map(function(word) {return word.toUpperCase()});
		var invalid = words.filter(function(word) {
			return word.split("").filter(function(char) {return char < 'A' || char > 'Z'}).length > 0;
		});
		if (invalid.length > 0) {
			throw "Words have invalid characters: " + invalid;
		}
		// len has to be big enough to accomodate the number of digits in the largest possible result.
		// If you multiply W N-digit numbers, the result will have on the order of W*N digits.
		len = maxlen(words) * words.length;
	}
	if (!callback) {
		callback = function (mapping, expression, pretty_expression) {
			console.log(hash_string(mapping) + "\n" + pretty_expression);
		}
	}
	if (!operation) {
		operation = "+";
	}

	// Do one layer at a time.  Start with the units place and find all mappings
	// that satisfy that column.  Then, for all mappings that satisfy that column,
	// find all mappings that satisfy the tens and ones column.
	//
	// We do this recursively, so the way to find all mappings that satisfy the
	// N least significant place values, we loop over all mappings that satisfy
	// the N-1 least significate place values, then for each of those, we call
	// "do_layer" for the Nth place value.  do_layer will look at all possible
	// additional mappings needed for the new variables found in that Nth place
	// value.
	for (var jj = 1; jj < len; jj++) {
		for (var ii = 0; ii < words.length; ii++) {
			var word = words[ii];
			if (word.length > len-jj && !(word[word.length-len-jj] in mappings)) {
				solve_singleop(words, operation, function (submapping) {
					//console.log(submapping);
					do_layer(words, operation, len, submapping, callback);
				}, len-1, mappings);
				return;
			}
		}
	}
	do_layer(words, operation, len, mappings, callback);
}

//
// Do layer looks at a single column of the problem.  It assumes
// that we were giving a mapping that satisfies all the less-significant
// columns of the problem, and using that mapping, do_layer finds
// all new variables that need to be set for this column, and finds
// all the mappings that will satisfy those new variables.
//
function do_layer(words, operation, len, mappings, callback) {
	if (len) {
		for (var ii = 0; ii < words.length; ii++) {
			var word = words[ii];
			if (word.length >= len && !(word[word.length - len] in mappings)) {
				var char = word[word.length - len];
				//console.log("Missing " + char);
				var values = get_possible_values(char, words, mappings);
				values.forEach(function(value) {
					//console.log("Trying " + char + " = " + value);
					mappings[char] = value;
					do_layer(words, operation, len, mappings, callback);
					delete(mappings[char]);
				});
				return;
			}
		}
	}
	if (check_equal(words, operation, len, mappings)) {
		var expression = substitute(words.slice(0, words.length - 1).join(operation) + "=" + words[words.length - 1], mappings);
		callback(mappings, expression, pretty_expression(words, operation, mappings));
	}
}

// ---------------------------------------------------------- //
// Helper functions
//

function hash_string(hash) {
	return Object.keys(hash).map(function(key) {
		return key + ":" + hash[key];
	}).join(",");
}

function get_possible_values(char, words, mappings, values) {
	var rev_mappings = rev_hash(mappings);
	if (!values) {
		values = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9];
	}
	if (any(words, function(word) { return word[0] == char; })) {
		values = values.filter(function(elt) {return elt != 0});
	}
	return values.filter(function(elt) {return !(elt in rev_mappings)});
}

function rev_hash(hash) {
	var reverse = {};
	Object.keys(hash).forEach(function(key) {
		reverse[hash[key]] = key;
	});
	return reverse;
}

function any(array, predicate) {
	for (var ii = 0; ii < array.length; ii++) {
		if (predicate(array[ii])) {
			return true;
		}
	}
	return false;
}

function all(array, predicate) {
	for (var ii = 0; ii < array.length; ii++) {
		if (!predicate(array[ii])) {
			return false;
		}
	}
	return true;
}

function maxlen(array) {
	return array.map(function(word) {return word.length}).reduce(function(a, b) {
		if (a > b) {
			return a;
		} else {
			return b;
		}
	}, 0);
}

/*
// These functions break up check_equal into parts.
// They can be useful for debugging, but otherwise aren't used, so they
// are commented out.

function check_desired(words, operation, len, mappings) {
	var new_words = words.map(function(elt) {return elt.substring(elt.length-len, elt.length);});
	var desired = new_words[new_words.length-1];
	return Number(substitute(desired, mappings));
}

function check_result(words, operation, len, mappings) {
	var new_words = words.map(function(elt) {return elt.substring(elt.length-len, elt.length);});
	var operands = new_words.slice(0, new_words.length-1);
	operands = operands.map(function(word) {return Number(substitute(word, mappings))});
	var result;
	if (operation == "+") {
		result = operands.reduce(function(a, b) {return a + b;}, 0);
	} else if (operation == "*") {
		result = operands.reduce(function(a, b) {return a * b;}, 1);
	}
	return result % Math.pow(10, len);
}

function check_both(words, operation, len, mappings) {
	return check_desired(words, operation, len, mappings) == check_result(words, operation, len, mappings);
}
*/

// Check if the given mappings satisfy the least-significant <len> columns of
// the problem.
function check_equal(words, operation, len, mappings) {
	var new_words = words;
	if (len) {
		new_words = words.map(function(elt) {return elt.substring(elt.length - len, elt.length);});
	}
	var desired = new_words[new_words.length - 1];
	var operands = new_words.slice(0, new_words.length - 1);
	operands = operands.map(function(word) {return Number(substitute(word, mappings))});
	var result;
	if (operation == "+") {
		result = operands.reduce(function(a, b) {return a + b;}, 0);
	} else if (operation == "*") {
		result = operands.reduce(function(a, b) {return a * b;}, 1);
	} else {
		throw "Invalid operation '" + operation + "' should be either '+' or '*'";
	}
	if (len) {
		result = result % Math.pow(10, len);
	}
	return result == Number(substitute(desired, mappings));
}

// Return a string which is made up of a character repeated len times.
function repeat(char, len) {
	return Array(len+1).join(char);
}

// Return a string of length width by adding padding on the left side of word.
function pad(word, width, value) {
	if (!value) {
		value = " ";
	}
	return repeat(value, width - word.length) + word;
}

// Format an equation nicely so the place values line up
function pretty_expression(words, operator, mapping) {
	if (mapping) {
		words = words.map(function(word) {return substitute(word, mapping)});
	}
	var width = maxlen(words) + 2;
	words[words.length - 2] = operator + " " + words[words.length - 2];
	words.splice(words.length - 1, 0, repeat("-", width));
	return words.map(function(word) {return pad(word, width)}).join("\n");
}

// ---------------------------------------------------------- //

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
function solve_general(expression) {
	expression = expression.toUpperCase();
	var letters = make_letters(expression);
	var ntries = 0;
	permutations([0, 1, 2, 3, 4, 5, 6, 7, 8, 9], 0, letters.length, function(values) {
		var mapping = make_mapping(letters, values);
		if (check_expression(expression, mapping)) {
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

// ---------------------------------------------------------- //

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

function check_expression(expression, mapping) {
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
