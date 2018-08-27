/**
 * Pack into an array of structs: https://en.wikipedia.org/wiki/AOS_and_SOA
 * @param {Object} obj - An object made up of arrays of equal length that will be zipped up.
 */
export function pack(obj){
  const keys = Object.keys(obj);

  if (keys.length === 0) return [];

  const n = obj[keys[0]].length;

  let result = Array.from({length: n}, () => ({}));

  for (let key of keys) {
    const values = obj[key];
    if (values.length !== n) throw "The struct of arrays must all be of equal length.";
    for (let i = 0; i < n; ++i) result[i][key] = values[i];
  }

  return result;
}

