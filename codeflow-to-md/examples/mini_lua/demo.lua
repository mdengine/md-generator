-- Sample flow: a → b → c

function c()
end

function b()
    c()
end

function a()
    b()
end
